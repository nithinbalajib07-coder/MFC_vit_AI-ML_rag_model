"""
SMU FAQ Ingestion CLI Module
Runnable via: python -m app.ingest
Loads raw data.csv, validates rows, generates chunked documents, and builds the vector index.
"""

import sys
import os
import argparse
import logging

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ingestion import run_ingestion, load_raw_data, RAW_DATA_PATH
from src.embeddings import EmbeddingEngine
from src.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("app.ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest and index SMU FAQ dataset.")
    parser.add_argument("--csv", default="data.csv", help="Path to raw dataset CSV file (default: data.csv)")
    parser.add_argument("--output", default="data/processed/processed_documents.json", help="Path for processed documents JSON")
    parser.add_argument("--report", default="data/processed/ingestion_report.json", help="Path for ingestion report JSON")
    parser.add_argument("--build-index", action="store_true", default=True, help="Automatically build dense vector embeddings")
    args = parser.parse_args()

    csv_path = args.csv if os.path.exists(args.csv) else (RAW_DATA_PATH if os.path.exists(RAW_DATA_PATH) else "data.csv")
    print(f"\n=======================================================")
    print(f" [SMU FAQ Ingestion Pipeline]")
    print(f" Source CSV: {csv_path}")
    print(f"=======================================================")

    df = load_raw_data(csv_path)
    print(f"Loaded {len(df)} records. Validating and chunking...")

    docs, report = run_ingestion(raw_path=csv_path, output_path=args.output, report_path=args.report)
    print(f"\nIngestion Results:")
    print(f"  • Total Loaded:      {report['records_loaded']} rows")
    print(f"  • Valid Records:     {report['valid_records']}")
    print(f"  • Invalid Records:   {report['invalid_records_count']}")
    print(f"  • Duplicates:        {report['duplicate_records_skipped']}")
    print(f"  • Output Chunks:     {report['final_indexed_chunks']}")
    print(f"  • Documents Saved:   {args.output}")
    print(f"  • Report Saved:      {args.report}")

    if args.build_index:
        print("\nGenerating dense vector embeddings for vector store...")
        embed_engine = EmbeddingEngine()
        store = VectorStore()
        texts = [d["text"] for d in docs]
        vecs = embed_engine.encode(texts, batch_size=32)
        store.build_index(docs, vecs)
        print(f"Vector store successfully persisted {len(vecs)} vectors to {store.index_dir}.")

    print("=======================================================\n")


if __name__ == "__main__":
    main()
