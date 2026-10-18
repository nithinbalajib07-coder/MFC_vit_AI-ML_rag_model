"""
Cross-Encoder Reranker
Re-ranks top candidate passages using a deep Cross-Encoder model.
Processes query and passage jointly for superior contextual ranking.
"""

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL, device: str = None):
        self.model_name = model_name
        self.device = device
        self._st_cross_encoder = None
        self._hf_tokenizer = None
        self._hf_model = None
        self._init_model()

    def _init_model(self):
        """Attempts to load via sentence-transformers CrossEncoder or HuggingFace AutoModelForSequenceClassification."""
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading CrossEncoder: {self.model_name}")
            self._st_cross_encoder = CrossEncoder(self.model_name)
            logger.info("CrossEncoder loaded successfully.")
            return
        except Exception as e:
            logger.info(f"CrossEncoder from sentence-transformers not available ({e}), using HuggingFace directly.")

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            self.torch = torch
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading HuggingFace SequenceClassification: {self.model_name} on {self.device}")
            self._hf_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._hf_model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
            self._hf_model.eval()
            logger.info("HuggingFace SequenceClassification model loaded.")
        except Exception as e:
            logger.warning(f"Could not load neural cross-encoder ({e}). Reranker will fallback to term-overlap alignment.")
            self._hf_model = None

    def rerank(self, query: str, candidate_docs: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank a list of candidate documents against the query.
        Returns top_k re-ordered documents with 'rerank_score'.
        """
        if not candidate_docs:
            return []

        if len(candidate_docs) <= 1:
            return candidate_docs[:top_k]

        # Sentence-transformers cross-encoder
        if self._st_cross_encoder is not None:
            pairs = [
                [query, doc.get("text") or f"Question: {doc.get('question', '')}\nAnswer: {doc.get('answer', '')}"]
                for doc in candidate_docs
            ]
            scores = self._st_cross_encoder.predict(pairs)
            scored_docs = []
            for doc, score in zip(candidate_docs, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = round(float(score), 4)
                scored_docs.append(doc_copy)
            scored_docs.sort(key=lambda d: d["rerank_score"], reverse=True)
            return scored_docs[:top_k]

        # HuggingFace sequence classification
        if self._hf_model is not None and self._hf_tokenizer is not None:
            pairs = [[query, doc.get("text", "")] for doc in candidate_docs]
            with self.torch.no_grad():
                inputs = self._hf_tokenizer(
                    pairs, padding=True, truncation=True, max_length=512, return_tensors="pt"
                ).to(self.device)
                logits = self._hf_model(**inputs).logits
                # For ms-marco models, logit is single score or binary
                if logits.shape[1] == 1:
                    scores = self.torch.sigmoid(logits).squeeze(-1).cpu().tolist()
                else:
                    scores = self.torch.softmax(logits, dim=-1)[:, 1].cpu().tolist()

            scored_docs = []
            for doc, score in zip(candidate_docs, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = round(float(score), 4)
                scored_docs.append(doc_copy)
            scored_docs.sort(key=lambda d: d["rerank_score"], reverse=True)
            return scored_docs[:top_k]

        # Fallback term-density overlap reranker if model is unavailable
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in candidate_docs:
            text = (doc.get("question", "") + " " + doc.get("answer", "")).lower()
            overlap = sum(1 for w in query_words if w in text)
            score = overlap / max(len(query_words), 1)
            doc_copy = dict(doc)
            doc_copy["rerank_score"] = round(float(score), 4)
            scored_docs.append(doc_copy)

        scored_docs.sort(key=lambda d: d["rerank_score"], reverse=True)
        return scored_docs[:top_k]
