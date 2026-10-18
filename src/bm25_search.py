"""
BM25 Keyword Search Engine
Implements sparse BM25 retrieval for exact keyword matching (course codes, acronyms, specific terms).
"""

import math
import re
import json
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

STOPWORDS = {
    "where", "when", "what", "how", "who", "why", "which",
    "is", "are", "was", "were", "be", "been", "being",
    "the", "a", "an", "at", "in", "on", "of", "for", "to", "from",
    "by", "with", "about", "can", "could", "would", "should",
    "do", "does", "did", "i", "you", "my", "your", "me", "we",
    "located", "situated", "tell"
}


def tokenize(text: str) -> List[str]:
    """
    Alphanumeric tokenizer that normalizes hyphens and underscores to spaces
    to match both hyphenated and unhyphenated compound terms.
    """
    text = text.lower()
    return re.findall(r"\b[a-z0-9]{2,}\b", text.replace("-", " ").replace("_", " "))


class BM25SearchEngine:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0
        self.tokenized_corpus: List[List[str]] = []

    def fit(self, documents: List[Dict[str, Any]]):
        """Fit the BM25 model on documents."""
        self.documents = documents
        self.corpus_size = len(documents)
        self.tokenized_corpus = []
        self.doc_lengths = []
        self.doc_freqs = {}

        total_words = 0
        for doc in documents:
            # Combine question and answer text for indexing
            text_to_index = f"{doc.get('question', '')} {doc.get('answer', '')}"
            tokens = tokenize(text_to_index)
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_words += doc_len

            seen_terms = set(tokens)
            for term in seen_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_len = total_words / self.corpus_size if self.corpus_size > 0 else 1.0

        # Compute IDF with Robertson-Spärck Jones formula
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

        logger.info(f"BM25 index built with {self.corpus_size} documents and {len(self.idf)} unique terms.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search top-K documents using BM25 score."""
        query_tokens = tokenize(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        # Use content tokens if available to prevent generic stopwords from dominating
        content_tokens = [t for t in query_tokens if t not in STOPWORDS]
        active_tokens = content_tokens if content_tokens else query_tokens

        scores: List[float] = [0.0] * self.corpus_size

        for term in active_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for doc_idx, doc_tokens in enumerate(self.tokenized_corpus):
                # Count term occurrences in doc
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[doc_idx] += idf_val * (numerator / denominator)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in ranked_indices:
            score = scores[idx]
            if score > 0:
                doc_copy = dict(self.documents[idx])
                doc_copy["bm25_score"] = round(float(score), 4)
                results.append(doc_copy)

        return results
