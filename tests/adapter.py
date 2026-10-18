"""
Unified Test Adapter for SMU FAQ RAG Assistant
Provides uniform interfaces for all 15 QA evaluation sections.
Ensures tests isolate temporary indices and never mutate production state.
"""

import os
import sys
import shutil
import uuid
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure project root is in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ingestion import (
    clean_text,
    validate_record,
    infer_category,
    infer_subdomain,
    build_documents,
    run_ingestion as internal_run_ingestion,
)
from src.embeddings import EmbeddingEngine
from src.vector_store import VectorStore
from src.bm25_search import BM25SearchEngine
from src.hybrid_retriever import HybridRetriever
from src.reranker import CrossEncoderReranker
from src.generator import GroundedGenerator, UNANSWERABLE_FALLBACK
from src.cache import QueryCache
from src.safety import (
    canonicalize_text,
    sanitize_input,
    wrap_prompt_with_boundaries,
    sanitize_output,
    sanitize_document_content,
    check_personal_or_unsupported_scope,
)
from src.pipeline import RAGPipeline

logger = logging.getLogger("test_adapter")

# ----------------------------------------------------------------------------
# Gold Set Definitions (Hand-verified against 250-row CSV)
# ----------------------------------------------------------------------------
GOLD_SET = {
    "G1": {
        "row": 1,
        "question": "Where can I get tickets to SMU home games? How much do they cost? Are discounts available? How do I find more information?",
        "expected_faq_id": "SMU-FAQ-002",
        "gold_facts": ["free admission", "student", "not sold online"],
        "required_keywords": ["ticket", "game"],
    },
    "G2": {
        "row": 5,
        "question": "Where do I go if I have computer problems? Can I get my personal computer fixed on campus? Where is the ITSS Help Desk and when is it open?",
        "expected_faq_id": "SMU-FAQ-006",
        "gold_facts": ["ITSS Help Desk", "Loyola Academic 268"],
        "required_keywords": ["itss", "loyola"],
    },
    "G3": {
        "row": 20,
        "question": "What is SMUSA? How do I become a member? How much does it cost?",
        "expected_faq_id": "SMU-FAQ-021",
        "gold_facts": ["Saint Mary's University Students' Association", "membership fees"],
        "required_keywords": ["smusa"],
    },
    "G4": {
        "row": 27,
        "question": "When are tuition fees due? What are the penalties for late payment? How do I pay my fees?",
        "expected_faq_id": "SMU-FAQ-028",
        "gold_facts": ["September", "January", "420-5582", "service.centre@smu.ca"],
        "required_keywords": ["tuition", "due"],
    },
    "G5": {
        "row": 32,
        "question": "When didthe policy come into effect?",
        "expected_faq_id": "SMU-FAQ-033",
        "gold_facts": ["September 1, 2013"],
        "required_keywords": ["2013"],
    },
    "G6": {
        "row": 60,
        "question": "Who can file a complaint or concern? How do I make a report?",
        "expected_faq_id": "SMU-FAQ-061",
        "gold_facts": ["studentconduct@smu.ca"],
        "required_keywords": ["studentconduct"],
    },
    "G7": {
        "row": 79,
        "question": "How can I appeal my evaluation? When is the deadline to appeal?",
        "expected_faq_id": "SMU-FAQ-080",
        "gold_facts": ["transfer@smu.ca"],
        "required_keywords": ["transfer@smu.ca"],
    },
    "G8": {
        "row": 100,
        "question": "What's the difference between products labelled 'fragrance-free', 'scent-free' or 'unscented'?",
        "expected_faq_id": "SMU-FAQ-101",
        "gold_facts": ["no guarantee"],
        "required_keywords": ["fragrance"],
    },
    "G9": {
        "row": 116,
        "question": "When will the exam schedule be posted?",
        "expected_faq_id": "SMU-FAQ-117",
        "gold_facts": ["November", "March"],
        "required_keywords": ["november", "march"],
    },
    "G10": {
        "row": 117,
        "question": "Where is the exam schedule posted?",
        "expected_faq_id": "SMU-FAQ-118",
        "gold_facts": ["Self Service Banner"],
        "required_keywords": ["banner"],
    },
    "G11": {
        "row": 150,
        "question": "What are the requirements to be accepted into the Co-operative Education program?",
        "expected_faq_id": "SMU-FAQ-151",
        "gold_facts": ["45 credit hours", "2.5 CGPA"],
        "required_keywords": ["45", "2.5"],
    },
    "G12": {
        "row": 189,
        "question": "How do I receive mail in residence? What is my residence mailing address? What happens to my mail during the break?",
        "expected_faq_id": "SMU-FAQ-190",
        "gold_facts": ["5907 Gorsebrook Avenue", "B3H 1G3"],
        "required_keywords": ["gorsebrook", "b3h"],
    },
    "G13": {
        "row": 200,
        "question": "Can I get my blood drawn at the clinic?",
        "expected_faq_id": "SMU-FAQ-201",
        "gold_facts": ["No", "Nova Scotia Health"],
        "required_keywords": ["no"],
    },
    "G14": {
        "row": 219,
        "question": "Does the Counselling Centre have a male Clinician?",
        "expected_faq_id": "SMU-FAQ-220",
        "gold_facts": ["Yes"],
        "required_keywords": ["yes"],
    },
    "G15": {
        "row": 220,
        "question": "Does the Counselling Centre have a black therapist?",
        "expected_faq_id": "SMU-FAQ-221",
        "gold_facts": ["Not currently"],
        "required_keywords": ["currently"],
    },
    "G16": {
        "row": 221,
        "question": "Does the Counselling Centre have a WPATH certified therapist?",
        "expected_faq_id": "SMU-FAQ-222",
        "gold_facts": ["WPATH"],
        "required_keywords": ["wpath"],
    },
}

VERIFIED_OOS_TOPICS = [
    "shuttle",
    "astrophysics",
    "PhD",
    "weather",
    "Dallas",
    "Southern Methodist",
]


# Compatibility functions mapped to adapter
def load_raw_data(path: str) -> pd.DataFrame:
    return TestAdapter().load_dataset(path)

def categorize_record(q: str, a: str) -> str:
    return infer_category(q, a)

def chunk_document(record: Dict[str, Any], max_words: int = 250, **kwargs) -> List[Dict[str, Any]]:
    return TestAdapter().chunk_single_record(record, max_words=max_words, **kwargs)

def ingest_dataset(csv_path: str, output_path: str, report_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    docs, report = build_documents(df)
    report["total_loaded"] = report.get("records_loaded", len(df))
    report["invalid_records"] = report.get("invalid_records_count", 0)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return docs, report


class TestAdapter:
    """Centralized adapter to interface QA tests with system components."""

    def __init__(self, data_path: str = "data.csv"):
        self.data_path = data_path
        self._pipeline: Optional[RAGPipeline] = None

    def get_pipeline(self) -> RAGPipeline:
        if self._pipeline is None:
            self._pipeline = RAGPipeline()
        return self._pipeline

    # 1. Dataset Loading & Inspection
    def load_dataset(self, path: Optional[str] = None) -> pd.DataFrame:
        target = path or self.data_path
        if not os.path.exists(target) or os.path.getsize(target) == 0:
            raise ValueError(f"Target dataset file is missing or empty (0 bytes): {target}")
        df = pd.read_csv(target)
        if "question" not in df.columns or "answer" not in df.columns:
            missing = [c for c in ["question", "answer"] if c not in df.columns]
            raise ValueError(f"Dataset missing required column(s): {missing}")
        return df

    # 2. Ingestion & Preprocessing
    def run_ingestion(self, csv_path: str, output_dir: str) -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        processed_path = os.path.join(output_dir, "processed_documents.json")
        report_path = os.path.join(output_dir, "ingestion_report.json")
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            raise ValueError(f"Cannot ingest empty CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        docs, report = build_documents(df)
        report["total_loaded"] = report.get("records_loaded", len(df))
        report["invalid_records"] = report.get("invalid_records_count", 0)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, ensure_ascii=False)
        return {"report": report, "documents": docs, "paths": (processed_path, report_path)}

    def chunk_single_record(self, record: Dict[str, Any], max_words: int = 250, **kwargs) -> List[Dict[str, Any]]:
        df = pd.DataFrame([record])
        docs, _ = build_documents(df, max_chunk_words=max_words)
        return docs

    # 3. Embeddings & Isolated Vector Store
    def create_isolated_vector_store(self, temp_dir: Optional[str] = None) -> Tuple[VectorStore, EmbeddingEngine, str]:
        dir_path = temp_dir or os.path.join("tests", "fixtures", f"vec_{uuid.uuid4().hex[:8]}")
        os.makedirs(dir_path, exist_ok=True)
        store = VectorStore(index_dir=dir_path)
        engine = EmbeddingEngine()
        return store, engine, dir_path

    # 4. Dense Retrieval
    def retrieve_dense(self, query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        p = self.get_pipeline()
        clean_q, is_safe, _ = sanitize_input(query)
        if not is_safe or not clean_q.strip():
            return []
        q_vec = p.embedding_engine.encode(clean_q)
        return p.vector_store.search(q_vec, top_k=top_k, category_filter=category_filter)

    # 5. Sparse BM25 Retrieval
    def retrieve_sparse(self, query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        p = self.get_pipeline()
        clean_q, is_safe, _ = sanitize_input(query)
        if not is_safe or not clean_q.strip():
            return []
        res = p.bm25_engine.search(clean_q, top_k=top_k)
        if category_filter:
            res = [d for d in res if d.get("category") == category_filter]
        return res[:top_k]

    # 6. Hybrid RRF Retrieval
    def retrieve_hybrid(self, query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        p = self.get_pipeline()
        clean_q, is_safe, _ = sanitize_input(query)
        if not is_safe or not clean_q.strip():
            return []
        return p.retriever.retrieve(clean_q, top_k=top_k, mode="hybrid_rrf", category_filter=category_filter)

    # 7. Cross-Encoder Reranking
    def rerank_candidates(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        p = self.get_pipeline()
        if not p.reranker or len(candidates) <= 1:
            return candidates[:top_k]
        return p.reranker.rerank(query, candidates, top_k=top_k)

    # 8. End-to-End Pipeline Query
    def query(
        self,
        query: str,
        top_k: int = 3,
        retrieval_mode: str = "hybrid_rrf",
        use_reranker: bool = True,
        category_filter: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        p = self.get_pipeline()
        p.use_reranker = use_reranker
        return p.query(
            user_query=query,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            category_filter=category_filter,
            user_id=user_id,
        )

    # 9. Cache Operations
    def get_cache(self) -> QueryCache:
        return self.get_pipeline().cache

    def clear_cache(self):
        self.get_pipeline().cache.clear()

    # 10. Safety & Guardrails
    def test_safety(self, text: str) -> Tuple[str, bool, str]:
        return sanitize_input(text)

    def test_personal_scope(self, text: str) -> Tuple[bool, str]:
        return check_personal_or_unsupported_scope(text)
