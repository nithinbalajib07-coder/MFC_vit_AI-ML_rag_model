"""
Query & Response Cache
Implements both Exact Match LRU Caching and Semantic Similarity Caching.
Significantly reduces query latency and LLM inference cost.
"""

import time
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)


class QueryCache:
    def __init__(self, max_size: int = 100, semantic_threshold: float = 0.94):
        self.max_size = max_size
        self.semantic_threshold = semantic_threshold
        # Stores exact queries: {normalized_query: {"response": ..., "timestamp": ..., "sources": ...}}
        self.exact_cache: Dict[str, Dict[str, Any]] = {}
        # Stores semantic records: [{"query": ..., "vector": ..., "response": ..., "sources": ...}]
        self.semantic_cache: List[Dict[str, Any]] = []
        self.hits: int = 0
        self.misses: int = 0
        self.total_time_saved_ms: float = 0.0

    def _normalize(
        self,
        query: str,
        mode: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        base = " ".join(query.strip().lower().split())
        parts = []
        if mode:
            parts.append(f"m:{mode}")
        if category:
            parts.append(f"c:{category}")
        if user_id:
            parts.append(f"u:{user_id}")
        if parts:
            return f"{'|'.join(parts)}::{base}"
        return base

    def clear(self):
        """Invalidate all cached queries."""
        self.exact_cache.clear()
        self.semantic_cache.clear()
        logger.info("QueryCache cleared completely.")

    def invalidate(
        self,
        query: Optional[str] = None,
        mode: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Invalidate a specific query or user namespace."""
        if query is None:
            self.clear()
            return

        base = " ".join(query.strip().lower().split())
        if mode is None and category is None and user_id is None:
            to_delete = [k for k in self.exact_cache if k == base or k.endswith(f"::{base}")]
            for k in to_delete:
                del self.exact_cache[k]
            self.semantic_cache = [
                item for item in self.semantic_cache
                if " ".join(item.get("query", "").strip().lower().split()) != base
            ]
        else:
            norm_q = self._normalize(query, mode=mode, category=category, user_id=user_id)
            if norm_q in self.exact_cache:
                del self.exact_cache[norm_q]
            self.semantic_cache = [
                item for item in self.semantic_cache
                if self._normalize(item["query"], mode=item.get("mode"), category=item.get("category"), user_id=item.get("user_id")) != norm_q
            ]

    def get(
        self,
        query: str,
        query_vector: Optional[np.ndarray] = None,
        mode: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        Check if query is cached.
        Returns (cached_result, hit_type) where hit_type is 'exact' or 'semantic', or None.
        """
        norm_q = self._normalize(query, mode=mode, category=category, user_id=user_id)

        # 1. Exact match check (O(1))
        if norm_q in self.exact_cache:
            self.hits += 1
            self.total_time_saved_ms += 1200.0  # Approx LLM turnaround saved
            logger.info(f"Cache HIT [Exact]: '{query}' (mode={mode})")
            return self.exact_cache[norm_q], "exact"

        # 2. Semantic match check (if query vector provided)
        if query_vector is not None and len(self.semantic_cache) > 0:
            for item in reversed(self.semantic_cache):
                if item.get("user_id") != user_id or item.get("mode") != mode:
                    continue
                similarity = float(np.dot(item["vector"], query_vector))
                if similarity >= self.semantic_threshold:
                    self.hits += 1
                    self.total_time_saved_ms += 1100.0
                    logger.info(f"Cache HIT [Semantic sim={similarity:.3f}]: '{query}' matches '{item['query']}'")
                    # Also store into exact cache for next time
                    self.exact_cache[norm_q] = item["response_data"]
                    return item["response_data"], f"semantic ({similarity:.2f})"

        self.misses += 1
        return None

    def set(
        self,
        query: str,
        response_data: Dict[str, Any],
        query_vector: Optional[np.ndarray] = None,
        mode: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Store a query response in both exact and semantic caches."""
        norm_q = self._normalize(query, mode=mode, category=category, user_id=user_id)

        # Evict oldest if capacity exceeded
        if len(self.exact_cache) >= self.max_size:
            oldest_key = next(iter(self.exact_cache))
            del self.exact_cache[oldest_key]

        self.exact_cache[norm_q] = response_data

        if query_vector is not None:
            if len(self.semantic_cache) >= self.max_size:
                self.semantic_cache.pop(0)
            self.semantic_cache.append({
                "query": query,
                "user_id": user_id,
                "mode": mode,
                "category": category,
                "vector": query_vector,
                "response_data": response_data
            })

    def get_stats(self) -> Dict[str, Any]:
        """Return cache telemetry metrics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_pct": round(hit_rate, 2),
            "est_time_saved_sec": round(self.total_time_saved_ms / 1000.0, 2),
            "cached_entries": len(self.exact_cache)
        }
