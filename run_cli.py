"""
Interactive CLI for SMU FAQ RAG Assistant
Allows interactive queries, inspects retrieved citations, tests prompt injections, and shows cache metrics.
"""

import sys
import logging
from src.pipeline import RAGPipeline

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)


def print_banner():
    print("=" * 70)
    print(" [SMU] Saint Mary's University Knowledge Assistant (RAG Pipeline)")
    print(" Type your question, or 'stats' for cache metrics, or 'exit' to quit.")
    print("=" * 70)


def format_cli_response(result: dict):
    print("\n" + "-" * 70)
    print(f"Latency: {result['latency_ms']} ms | Cached: {result['cached']} | Grounded: {result['is_grounded']}")
    print(f"Backend: {result['backend']} | Mode: {result['mode']} | Confidence: {result['confidence']}")
    print("-" * 70)
    print(f"\n{result['answer']}\n")

    if result.get("sources"):
        print("Supporting Sources & Citations:")
        for s in result["sources"]:
            print(f"  * [{s['faq_id']}] {s['question']}")
            print(f"    Snippet: {s['snippet']}")
            print(f"    Score: {s['score']}\n")
    print("-" * 70 + "\n")


def main():
    print("Loading SMU FAQ RAG Pipeline...")
    pipeline = RAGPipeline()
    print_banner()

    # If argument provided on command line, run once and exit
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nQuery: {query}")
        res = pipeline.query(query)
        format_cli_response(res)
        return

    while True:
        try:
            user_input = input("SMU Query > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            if user_input.lower() == "stats":
                stats = pipeline.cache.get_stats()
                print("\n📊 Cache Performance Telemetry:")
                for k, v in stats.items():
                    print(f"  {k}: {v}")
                print()
                continue

            result = pipeline.query(user_input)
            format_cli_response(result)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
