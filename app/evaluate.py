"""
Evaluation Runner Module
Runnable via: python -m app.evaluate
Evaluates Dense Baseline, BM25, Hybrid RRF, and Hybrid + Reranker on fixed gold test queries.
Outputs Hit@1, Hit@3, Hit@5, MRR, latency, and ablation comparison.
"""

import sys
import os
import time
import json
import logging

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from tests.adapter import TestAdapter, GOLD_SET

logging.basicConfig(level=logging.WARNING)


def run_benchmark():
    adapter = TestAdapter()
    print("\n" + "=" * 76)
    print("  SMU FAQ RAG Assistant — Retrieval Evaluation & Ablation Benchmark")
    print(f"  Evaluating {len(GOLD_SET)} hand-verified Gold Queries across 4 configurations")
    print("=" * 76)

    configs = [
        ("Dense Baseline (all-MiniLM-L6-v2)", "dense_only", False),
        ("Sparse Keyword (BM25Okapi)", "sparse_only", False),
        ("Hybrid RRF (Dense 0.6 + BM25 0.4)", "hybrid_rrf", False),
        ("Hybrid RRF + Cross-Encoder Reranker", "hybrid_rrf", True),
    ]

    results_table = []

    for name, mode, use_rr in configs:
        t0 = time.time()
        hit1, hit3, hit5 = 0, 0, 0
        rr_scores = []
        latencies = []

        for gid, gdata in GOLD_SET.items():
            q_start = time.time()
            if mode == "dense_only":
                res = adapter.retrieve_dense(gdata["question"], top_k=5)
            elif mode == "sparse_only":
                res = adapter.retrieve_sparse(gdata["question"], top_k=5)
            else:
                res = adapter.retrieve_hybrid(gdata["question"], top_k=5)

            if use_rr and len(res) > 1:
                res = adapter.rerank_candidates(gdata["question"], res, top_k=5)

            latencies.append((time.time() - q_start) * 1000)
            ret_ids = [d.get("faq_id") for d in res]
            expected = gdata["expected_faq_id"]
            targets = expected if isinstance(expected, list) else [expected]

            rank = next((i for i, did in enumerate(ret_ids, 1) if did in targets), 0)
            if rank == 1:
                hit1 += 1
            if 1 <= rank <= 3:
                hit3 += 1
            if 1 <= rank <= 5:
                hit5 += 1
            rr_scores.append(1.0 / rank if rank > 0 else 0.0)

        n = len(GOLD_SET)
        avg_lat = sum(latencies) / len(latencies)
        mrr = sum(rr_scores) / n

        results_table.append({
            "config": name,
            "hit1": hit1 / n * 100,
            "hit3": hit3 / n * 100,
            "hit5": hit5 / n * 100,
            "mrr": mrr,
            "avg_latency_ms": avg_lat,
        })

    print("\nBenchmark Results Table:")
    print("-" * 76)
    print(f"{'Configuration':<38} | {'Hit@1':<6} | {'Hit@3':<6} | {'Hit@5':<6} | {'MRR':<6} | {'Avg Lat':<8}")
    print("-" * 76)
    for r in results_table:
        print(f"{r['config']:<38} | {r['hit1']:>5.1f}% | {r['hit3']:>5.1f}% | {r['hit5']:>5.1f}% | {r['mrr']:>6.3f} | {r['avg_latency_ms']:>6.1f}ms")
    print("-" * 76)

    # Save to JSON
    os.makedirs("reports", exist_ok=True)
    out_file = os.path.join("reports", "evaluation_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_table, f, indent=2)
    print(f"\nResults saved to {out_file}\n")


if __name__ == "__main__":
    run_benchmark()
