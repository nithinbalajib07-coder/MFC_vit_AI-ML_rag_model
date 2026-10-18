"""
Hybrid Retriever (Dense Vector + BM25 Sparse Search)
Implements Reciprocal Rank Fusion (RRF) and Normalized Weighted Fusion.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from src.bm25_search import BM25SearchEngine
from src.vector_store import VectorStore
from src.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        vector_store: VectorStore,
        bm25_engine: BM25SearchEngine,
        embedding_engine: EmbeddingEngine,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.bm25_engine = bm25_engine
        self.embedding_engine = embedding_engine
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        mode: str = "hybrid_rrf",
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using specified mode:
        - 'dense_only': Semantic vector search only
        - 'sparse_only': BM25 keyword search only
        - 'hybrid_rrf': Reciprocal Rank Fusion combining both
        """
        # Fetch dense candidates
        dense_results = []
        if mode in ["dense_only", "hybrid_rrf"]:
            query_vector = self.embedding_engine.encode(query)
            dense_results = self.vector_store.search(
                query_vector, top_k=top_k * 2, category_filter=category_filter
            )

        if mode == "dense_only":
            return dense_results[:top_k]

        # Fetch sparse candidates
        sparse_results = []
        if mode in ["sparse_only", "hybrid_rrf"]:
            sparse_results = self.bm25_engine.search(query, top_k=top_k * 2)
            if category_filter:
                sparse_results = [d for d in sparse_results if d.get("category") == category_filter]

        if mode == "sparse_only":
            return sparse_results[:top_k]

        # Mode: 'hybrid_rrf' (Reciprocal Rank Fusion)
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # 1. Score dense rankings
        for rank, doc in enumerate(dense_results, 1):
            doc_id = doc["doc_id"]
            doc_map[doc_id] = doc
            rrf_score = self.dense_weight / (self.rrf_k + rank)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score

        # 2. Score sparse rankings
        for rank, doc in enumerate(sparse_results, 1):
            doc_id = doc["doc_id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
            rrf_score = self.sparse_weight / (self.rrf_k + rank)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score

        # 3. Sort by total RRF score
        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)

        results = []
        for did in sorted_doc_ids[:top_k]:
            merged_doc = dict(doc_map[did])
            merged_doc["rrf_score"] = round(float(rrf_scores[did]), 5)
            results.append(merged_doc)

        return results
