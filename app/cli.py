"""
SMU FAQ CLI Query Module
Runnable via: python -m app.cli --query "Where can I get the academic calendar?"
Or interactively: python -m app.cli
"""

import sys
import os
import argparse
import logging

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import RAGPipeline

logging.basicConfig(level=logging.WARNING)


def format_cli_output(result: dict):
    print("\n" + "=" * 72)
    print(f" Query: {result.get('query', '')}")
    print(f" Mode: {result.get('mode', '')} | Latency: {result.get('latency_ms', 0)} ms | Cached: {result.get('cached', False)}")
    print(f" Grounded: {result.get('is_grounded', False)} | Confidence: {result.get('confidence', 0)} | Backend: {result.get('backend', '')}")
    print("-" * 72)
    print(f"\n{result.get('answer', '')}\n")

    sources = result.get("sources", [])
    if sources:
        print("Supporting Evidence & Citations:")
        for idx, s in enumerate(sources, 1):
            fid = s.get("faq_id", "SMU-FAQ")
            q = s.get("question", "")
            snippet = s.get("snippet", "")
            score = s.get("score", "")
            cat = s.get("category", "")
            print(f"  [{idx}] {fid} ({cat})")
            print(f"      Q: {q}")
            print(f"      Snippet: {snippet}")
            if score:
                print(f"      Score: {score}")
            print()
    print("=" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Query the SMU FAQ Knowledge Assistant.")
    parser.add_argument("--query", "-q", type=str, default=None, help="Direct query to execute")
    parser.add_argument("--mode", "-m", choices=["dense_only", "sparse_only", "hybrid_rrf"], default="hybrid_rrf", help="Retrieval mode (default: hybrid_rrf)")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="Number of evidence passages to retrieve (default: 3)")
    parser.add_argument("--category", "-c", type=str, default=None, help="Filter by university department/category")
    parser.add_argument("--stats", action="store_true", help="Print cache statistics and exit")
    args = parser.parse_args()

    pipeline = RAGPipeline(retrieval_mode=args.mode)

    if args.stats:
        stats = pipeline.cache.get_stats()
        print("\n=== Cache Telemetry ===")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print()
        return

    # Single-shot query execution
    if args.query:
        res = pipeline.query(args.query, top_k=args.top_k, retrieval_mode=args.mode, category_filter=args.category)
        format_cli_output(res)
        return

    # Interactive REPL mode
    print("=" * 72)
    print("  [SMU] Saint Mary's University Knowledge Assistant (CLI REPL)")
    print("  Type your question below. Type 'stats' for cache metrics, or 'exit' to quit.")
    print("=" * 72)

    while True:
        try:
            user_input = input("SMU > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting SMU Assistant.")
                break
            if user_input.lower() == "stats":
                stats = pipeline.cache.get_stats()
                print("\n=== Cache Telemetry ===")
                for k, v in stats.items():
                    print(f"  {k}: {v}")
                print()
                continue

            res = pipeline.query(user_input, top_k=args.top_k, retrieval_mode=args.mode, category_filter=args.category)
            format_cli_output(res)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    main()
