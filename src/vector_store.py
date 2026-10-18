"""
Vector Store Engine
Manages dense embedding storage, persistence, dimension validation, and cosine similarity vector search.
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = os.path.join("db", "vector_store")


class VectorStore:
    def __init__(self, index_dir: str = DEFAULT_INDEX_DIR):
        self.index_dir = index_dir
        self.vectors_file = os.path.join(index_dir, "embeddings.npy")
        self.metadata_file = os.path.join(index_dir, "metadata.json")
        self.embeddings: Optional[np.ndarray] = None
        self.documents: List[Dict[str, Any]] = []

    def build_index(self, documents: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Build and persist the vector index with validation.
        Rejects invalid dimensions or document-embedding count mismatches.
        """
        if len(documents) == 0:
            logger.warning("Attempted to build vector index with 0 documents.")
            self.documents = []
            self.embeddings = np.empty((0, 384), dtype=np.float32)
            return

        emb_array = np.array(embeddings, dtype=np.float32)
        if emb_array.ndim != 2:
            raise ValueError(f"Embeddings must be 2-dimensional (samples, dim), got ndim={emb_array.ndim}")
        if len(documents) != len(emb_array):
            raise ValueError(f"Document count ({len(documents)}) does not match embeddings count ({len(emb_array)})")

        os.makedirs(self.index_dir, exist_ok=True)
        self.documents = documents
        self.embeddings = emb_array

        # Save to disk
        np.save(self.vectors_file, self.embeddings)
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        logger.info(f"Vector store persisted {len(documents)} vectors (dim={emb_array.shape[1]}) to {self.index_dir}")

    def load_index(self) -> bool:
        """Load persisted index from disk if present."""
        if os.path.exists(self.vectors_file) and os.path.exists(self.metadata_file):
            self.embeddings = np.load(self.vectors_file)
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            logger.info(f"Loaded vector store with {len(self.documents)} items from {self.index_dir}")
            return True
        return False

    def delete(self, doc_ids: List[str]) -> int:
        """
        Delete documents by doc_id (or faq_id) from index and persist updated vectors.
        Returns count of deleted chunks.
        """
        if self.embeddings is None or len(self.documents) == 0 or not doc_ids:
            return 0

        target_set = set(doc_ids)
        keep_indices = []
        deleted_count = 0

        for i, doc in enumerate(self.documents):
            did = doc.get("doc_id")
            fid = doc.get("faq_id")
            if did in target_set or fid in target_set:
                deleted_count += 1
            else:
                keep_indices.append(i)

        if deleted_count > 0:
            self.documents = [self.documents[i] for i in keep_indices]
            if len(keep_indices) > 0:
                self.embeddings = self.embeddings[keep_indices]
            else:
                self.embeddings = np.empty((0, self.embeddings.shape[1]), dtype=np.float32)

            # Persist updated index
            os.makedirs(self.index_dir, exist_ok=True)
            np.save(self.vectors_file, self.embeddings)
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            logger.info(f"Deleted {deleted_count} documents from vector store. Remaining: {len(self.documents)}")

        return deleted_count

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Cosine similarity search over indexed embeddings with dimension validation.
        Vectors are assumed normalized.
        """
        if top_k <= 0:
            return []

        if self.embeddings is None or len(self.documents) == 0:
            logger.warning("Vector store is empty.")
            return []

        q_vec = np.array(query_vector, dtype=np.float32).ravel()
        if q_vec.shape[0] != self.embeddings.shape[1]:
            logger.error(
                f"Vector dimension mismatch: query dim {q_vec.shape[0]} != index dim {self.embeddings.shape[1]}"
            )
            raise ValueError(
                f"Vector dimension mismatch: query dim {q_vec.shape[0]} != index dim {self.embeddings.shape[1]}"
            )

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.embeddings, q_vec)
        
        # Rank by score descending
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < score_threshold:
                continue

            doc = self.documents[idx]
            if category_filter and doc.get("category") != category_filter:
                continue

            doc_copy = dict(doc)
            doc_copy["vector_score"] = round(score, 4)
            results.append(doc_copy)

            if len(results) >= top_k:
                break

        return results
