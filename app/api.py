"""
FastAPI REST API for SMU FAQ Knowledge Assistant
Endpoints:
  GET  /health     - System health, corpus statistics, and model readiness
  POST /query      - Execute grounded RAG query with verified citations
  POST /evaluate   - Run evaluation suite and return benchmark metrics
Runnable via: uvicorn app.api:app --reload
"""

import sys
import os
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.pipeline import RAGPipeline
from src.safety import sanitize_input

app = FastAPI(
    title="SMU FAQ Knowledge Assistant API",
    description="Official Grounded RAG REST API for Saint Mary's University (Halifax)",
    version="1.0.0",
)

# CORS Security Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_pipeline_instance: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance


# ----------------------------------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------------------------------
class SourceCitation(BaseModel):
    faq_id: str = Field(..., description="Document identifier (e.g. SMU-FAQ-002)")
    question: str = Field(..., description="Original university FAQ question")
    snippet: str = Field(..., description="Verbatim text snippet from official documentation")
    category: Optional[str] = Field(None, description="University operational domain")
    score: Optional[Any] = Field(None, description="Relevance ranking score")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="University student or staff question")
    top_k: int = Field(3, ge=1, le=20, description="Maximum number of evidence sources to return")
    mode: str = Field("hybrid_rrf", description="Retrieval mode: 'dense_only', 'sparse_only', or 'hybrid_rrf'")
    category_filter: Optional[str] = Field(None, description="Optional university department filter")
    user_id: Optional[str] = Field(None, description="Optional user session identifier for caching")


class QueryResponse(BaseModel):
    query: str
    answer: str
    is_grounded: bool
    abstained: bool
    confidence: float
    sources: List[SourceCitation]
    retrieval_mode: str
    cached: bool
    latency_ms: float
    backend: str


class HealthResponse(BaseModel):
    status: str
    institution: str
    total_indexed_chunks: int
    models_loaded: Dict[str, str]
    cache_stats: Dict[str, Any]


class EvaluateRequest(BaseModel):
    top_k: int = Field(5, ge=1, le=10)
    modes: List[str] = Field(["dense_only", "hybrid_rrf"], description="Retrieval modes to benchmark")


# ----------------------------------------------------------------------------
# REST Endpoints
# ----------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
def health_check():
    """Returns system status, document count, and index readiness."""
    p = get_pipeline()
    return {
        "status": "healthy",
        "institution": "Saint Mary's University (Halifax, NS)",
        "total_indexed_chunks": len(p.documents),
        "models_loaded": {
            "embeddings": p.embedding_engine.model_name,
            "reranker": p.reranker.model_name if p.reranker else "none",
            "generator": p.generator.active_backend,
        },
        "cache_stats": p.cache.get_stats(),
    }


@app.post("/query", response_model=QueryResponse, tags=["Retrieval"])
def execute_query(req: QueryRequest):
    """
    Executes grounded RAG retrieval and generation.
    Returns answer, citations, confidence score, and latency.
    """
    clean_q = req.query.strip()
    if not clean_q:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty or whitespace.",
        )

    if len(req.query) > 5000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Query length exceeds maximum limit (5000 characters).",
        )

    p = get_pipeline()
    res = p.query(
        user_query=req.query,
        top_k=req.top_k,
        retrieval_mode=req.mode,
        category_filter=req.category_filter,
        user_id=req.user_id,
    )

    sources_list = [
        SourceCitation(
            faq_id=s.get("faq_id", "SMU-FAQ"),
            question=s.get("question", ""),
            snippet=s.get("snippet", ""),
            category=s.get("category"),
            score=s.get("score"),
        )
        for s in res.get("sources", [])
    ]

    return QueryResponse(
        query=res.get("query", req.query),
        answer=res.get("answer", ""),
        is_grounded=res.get("is_grounded", False),
        abstained=res.get("abstained", False),
        confidence=res.get("confidence", 0.0),
        sources=sources_list,
        retrieval_mode=res.get("mode", req.mode),
        cached=res.get("cached", False),
        latency_ms=res.get("latency_ms", 0.0),
        backend=res.get("backend", "local"),
    )


@app.post("/evaluate", tags=["Evaluation"])
def run_evaluation(req: EvaluateRequest):
    """
    Executes retrieval evaluation across the gold-standard test benchmarks.
    """
    from tests.adapter import TestAdapter, GOLD_SET
    adapter = TestAdapter()

    metrics = {}
    for mode in req.modes:
        t0 = time.time()
        hits_1, hits_3, hits_5 = 0, 0, 0
        rr_list = []

        for gid, gdata in GOLD_SET.items():
            if mode == "dense_only":
                res = adapter.retrieve_dense(gdata["question"], top_k=req.top_k)
            else:
                res = adapter.retrieve_hybrid(gdata["question"], top_k=req.top_k)

            ret_ids = [d.get("faq_id") for d in res]
            expected = gdata["expected_faq_id"]
            targets = expected if isinstance(expected, list) else [expected]
            rank = next((i for i, did in enumerate(ret_ids, 1) if did in targets), 0)

            if rank == 1:
                hits_1 += 1
            if 1 <= rank <= 3:
                hits_3 += 1
            if 1 <= rank <= 5:
                hits_5 += 1
            rr_list.append(1.0 / rank if rank > 0 else 0.0)

        n = len(GOLD_SET)
        metrics[mode] = {
            "hit_at_1": round(hits_1 / n, 3),
            "hit_at_3": round(hits_3 / n, 3),
            "hit_at_5": round(hits_5 / n, 3),
            "mrr": round(sum(rr_list) / n, 3),
            "eval_latency_sec": round(time.time() - t0, 2),
        }

    return {
        "status": "success",
        "gold_benchmarks_count": len(GOLD_SET),
        "results": metrics,
    }
