"""
Build & Precompute Vector + BM25 Indexes
Loads the 256 document chunks from the SMU FAQ dataset and embeds them into the vector database.
"""

import os
import json
import time
import logging
from src.ingestion import run_ingestion
from src.embeddings import EmbeddingEngine
from src.vector_store import VectorStore
from src.bm25_search import BM25SearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    start_t = time.time()
    logger.info("Starting index build process...")

    # 1. Ingest & Preprocess
    res = run_ingestion()
    docs = res[0] if isinstance(res, tuple) else res

    # 2. Build BM25 Index
    bm25 = BM25SearchEngine()
    bm25.fit(docs)

    # 3. Dense Embedding Generation
    embedding_engine = EmbeddingEngine()
    texts = [doc["text"] for doc in docs]
    logger.info(f"Generating dense embeddings for {len(texts)} documents using {embedding_engine.model_name}...")
    embeddings = embedding_engine.encode(texts, batch_size=32)
    logger.info(f"Embeddings shape: {embeddings.shape}")

    # 4. Save to Vector Store
    vector_store = VectorStore()
    vector_store.build_index(docs, embeddings)

    elapsed = time.time() - start_t
    logger.info(f"Indexing successfully completed in {elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()
