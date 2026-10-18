"""
End-to-End RAG Pipeline Orchestrator
Coordinates cache, safety sanitization, hybrid retrieval, reranking, and generation.
"""

import time
import math
import json
import logging
from typing import Dict, Any, Optional, List
from src.bm25_search import BM25SearchEngine
from src.vector_store import VectorStore
from src.embeddings import EmbeddingEngine
from src.hybrid_retriever import HybridRetriever
from src.reranker import CrossEncoderReranker
from src.cache import QueryCache
from src.safety import sanitize_input, wrap_prompt_with_boundaries, sanitize_output, check_personal_or_unsupported_scope
from src.generator import GroundedGenerator
from src.query_expander import QueryExpander

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(
        self,
        docs_path: str = "data/processed/processed_documents.json",
        use_reranker: bool = True,
        retrieval_mode: str = "hybrid_rrf",
    ):
        self.docs_path = docs_path
        self.use_reranker = use_reranker
        self.retrieval_mode = retrieval_mode

        logger.info("Initializing RAG Pipeline components...")
        self.cache = QueryCache()
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore()
        self.bm25_engine = BM25SearchEngine()
        self.generator = GroundedGenerator()
        self.expander = QueryExpander()

        # Load documents and initialize indexes
        self._load_or_build_indexes()

        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_engine=self.bm25_engine,
            embedding_engine=self.embedding_engine,
        )

        if self.use_reranker:
            self.reranker = CrossEncoderReranker()
        else:
            self.reranker = None

        logger.info("RAG Pipeline is fully initialized and ready.")

    def _load_or_build_indexes(self):
        """Loads processed documents and builds/loads vector + BM25 indexes."""
        with open(self.docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        # 1. BM25 index (in-memory, instant)
        self.bm25_engine.fit(self.documents)

        # 2. Vector index (load if exists, otherwise build)
        if not self.vector_store.load_index():
            logger.info("Building dense vector embeddings for documents...")
            texts_to_embed = [doc["text"] for doc in self.documents]
            embeddings = self.embedding_engine.encode(texts_to_embed, batch_size=32)
            self.vector_store.build_index(self.documents, embeddings)

    def query(
        self,
        user_query: str,
        top_k: int = 3,
        retrieval_mode: Optional[str] = None,
        category_filter: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute end-to-end query answering pipeline.
        """
        start_time = time.time()
        mode = retrieval_mode or self.retrieval_mode

        # Step 1: Safety & Prompt Injection Check
        clean_q, is_safe, reason = sanitize_input(user_query)
        if not is_safe:
            return {
                "query": user_query,
                "answer": f"Request rejected by university security policy: {reason}",
                "is_grounded": False,
                "sources": [],
                "cached": False,
                "backend": "safety_guard",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "mode": mode,
                "confidence": 0.0,
            }

        # Step 1.5: Personal Scope & Unsupported Invariant Check (Rule B & Rule E)
        is_personal, refusal_msg = check_personal_or_unsupported_scope(clean_q)
        if is_personal:
            return {
                "query": user_query,
                "answer": refusal_msg,
                "abstained": True,
                "is_grounded": False,
                "sources": [],
                "cached": False,
                "backend": "policy_guard",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "mode": mode,
                "confidence": 0.0,
            }

        # Step 2: Query Embedding & Cache Check (Fast exact lookup first, partitioned by mode)
        cached_exact = self.cache.get(clean_q, query_vector=None, mode=mode, category=category_filter, user_id=user_id)
        if cached_exact is not None:
            res_data, hit_type = cached_exact
            return {
                **res_data,
                "cached": True,
                "cache_hit_type": hit_type,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        query_vector = self.embedding_engine.encode(clean_q)
        cached_result = self.cache.get(clean_q, query_vector=query_vector, mode=mode, category=category_filter, user_id=user_id)
        if cached_result is not None:
            res_data, hit_type = cached_result
            return {
                **res_data,
                "cached": True,
                "cache_hit_type": hit_type,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 2.5: Semantic Query Expansion & Intent Normalization
        search_q = self.expander.expand_query(clean_q)

        # Step 3: Retrieval (Dense, Sparse, or Hybrid RRF)
        retrieved_candidates = self.retriever.retrieve(
            search_q,
            top_k=top_k * 3 if self.use_reranker else top_k,
            mode=mode,
            category_filter=category_filter,
        )

        # Step 4: Reranking (Cross-Encoder)
        if self.use_reranker and self.reranker and len(retrieved_candidates) > 1:
            final_docs = self.reranker.rerank(search_q, retrieved_candidates, top_k=top_k)
        else:
            final_docs = retrieved_candidates[:top_k]

        # Calculate retrieval confidence score via calibrated probability
        if final_docs:
            top_doc = final_docs[0]
            vec_score = float(top_doc.get("vector_score", 0.0))
            if "rerank_score" in top_doc:
                # Calibrate cross-encoder logit to [0, 1] probability
                try:
                    s = float(top_doc["rerank_score"])
                    base_prob = 1.0 / (1.0 + math.exp(-(s + 2.5)))
                    # When dense vector similarity is strong (>= 0.50), incorporate verified semantic signal
                    if vec_score >= 0.50:
                        confidence = round(max(base_prob, min(vec_score, 0.95)), 3)
                    elif s >= -4.2 and vec_score >= 0.40:
                        confidence = round(max(base_prob, min(vec_score, 0.95)), 3)
                    else:
                        confidence = round(base_prob, 3)
                except (TypeError, ValueError, OverflowError):
                    confidence = 0.0
            else:
                raw_score = top_doc.get("vector_score", top_doc.get("rrf_score", 0.5))
                try:
                    confidence = round(float(raw_score), 3)
                except (TypeError, ValueError):
                    confidence = 0.0
        else:
            confidence = 0.0

        # Step 5: Construct Prompt with XML Boundaries & Generate Answer
        context_str = self.generator._format_context(final_docs)
        prompt_with_boundaries = wrap_prompt_with_boundaries(context_str, clean_q)

        gen_result = self.generator.generate(
            query=clean_q,
            retrieved_docs=final_docs,
            confidence_score=confidence,
            full_prompt=prompt_with_boundaries,
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)
        sanitized_answer = sanitize_output(gen_result["answer"])

        response_payload = {
            "query": user_query,
            "answer": sanitized_answer,
            "abstained": not gen_result["is_grounded"],
            "is_grounded": gen_result["is_grounded"],
            "sources": gen_result["sources"],
            "backend": gen_result["backend"],
            "confidence": gen_result["confidence"],
            "mode": mode,
            "cached": False,
            "latency_ms": latency_ms,
        }

        # Store in Cache if grounded
        if gen_result["is_grounded"]:
            self.cache.set(clean_q, response_payload, query_vector=query_vector, mode=mode, category=category_filter, user_id=user_id)

        return response_payload
