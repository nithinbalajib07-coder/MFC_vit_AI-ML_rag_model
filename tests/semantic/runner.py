"""
Semantic Retrieval, Paraphrase, Synonym & Multi-Stage Diagnostic Test Runner
Evaluates and benchmarks the RAG system on:
1. Cafeteria and dining paraphrases (all prompt queries)
2. Low lexical overlap synonyms across university topics
3. Typos, shorthand, and conversational phrasing
4. Entity preservation
5. Unanswerable question abstentions
6. Security / adversarial prompt injection + semantic questions
Tracks dense, BM25, hybrid RRF, reranking, and generation stages.
"""

import os
import sys
import json
import time
import logging
import numpy as np
from typing import List, Dict, Any

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, WORKSPACE_ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import RAGPipeline
from src.safety import sanitize_input
from tests.semantic.test_cases import SEMANTIC_TEST_CASES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_semantic_evaluation():
    print("=" * 110)
    print(" EXECUTING COMPREHENSIVE SEMANTIC RETRIEVAL, SYNONYM & PARAPHRASE AUDIT SUITE")
    print("=" * 110)

    pipeline = RAGPipeline()
    retriever = pipeline.retriever
    reranker = pipeline.reranker
    expander = pipeline.expander

    test_results = []
    category_stats: Dict[str, Dict[str, Any]] = {}

    # Retrieval metrics on answerable queries
    answerable_count = 0
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    mrr_sum = 0.0
    correct_grounded = 0
    correct_abstentions = 0
    latencies = []

    print(f"\nRunning {len(SEMANTIC_TEST_CASES)} semantic test cases across 6 operational categories...\n")

    for tc in SEMANTIC_TEST_CASES:
        t_id = tc["test_id"]
        cat = tc["category"]
        query = tc["query"]
        expected_faqs = tc["expected_faq_ids"]
        expect_abstain = tc["expect_abstain"]
        expect_grounded = tc["expect_grounded"]
        req_keywords = tc.get("required_keywords", [])
        forbid_keywords = tc.get("forbidden_keywords", [])

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "pass": 0, "fail": 0}
        category_stats[cat]["total"] += 1

        t0 = time.time()

        # Step A: Diagnostics - Query Sanitization & Expansion
        clean_input, _, _ = sanitize_input(query)
        search_q = expander.expand_query(clean_input)

        # Step B: Diagnostics - Dense Retrieval
        dense_cands = retriever.retrieve(search_q, top_k=5, mode="dense_only")
        dense_ids = [d.get("faq_id") for d in dense_cands]
        dense_scores = [round(float(d.get("vector_score", 0.0)), 4) for d in dense_cands]

        # Step C: Diagnostics - BM25 Sparse Retrieval
        bm25_cands = retriever.retrieve(search_q, top_k=5, mode="sparse_only")
        bm25_ids = [d.get("faq_id") for d in bm25_cands]
        bm25_scores = [round(float(d.get("bm25_score", 0.0)), 4) for d in bm25_cands]

        # Step D: Diagnostics - Hybrid RRF Retrieval
        hybrid_cands = retriever.retrieve(search_q, top_k=10, mode="hybrid_rrf")
        hybrid_ids = [d.get("faq_id") for d in hybrid_cands]

        # Step E: Diagnostics - Cross-Encoder Reranking
        if reranker and hybrid_cands:
            reranked_cands = reranker.rerank(search_q, hybrid_cands, top_k=5)
        else:
            reranked_cands = hybrid_cands[:5]
        reranked_ids = [d.get("faq_id") for d in reranked_cands]
        reranked_scores = [round(float(d.get("rerank_score", 0.0)), 4) for d in reranked_cands]

        # Step F: End-to-End Pipeline Query Execution
        # We clear cache entry for testing to measure clean generation
        pipeline.cache.clear()
        res = pipeline.query(query, top_k=3)
        lat = (time.time() - t0) * 1000.0
        latencies.append(lat)

        ans = res.get("answer", "")
        grounded = res.get("is_grounded", False)
        sources = [s.get("faq_id") for s in res.get("sources", [])]
        confidence = res.get("confidence", 0.0)

        # Validation Logic
        passed = True
        fail_reasons = []

        if expect_abstain:
            if grounded:
                passed = False
                fail_reasons.append("Expected abstention on unanswerable query, but system provided grounded answer")
            else:
                correct_abstentions += 1
        else:
            answerable_count += 1
            # Check retrieval match in top reranked results
            matched_rank = None
            if expected_faqs:
                for idx, fid in enumerate(reranked_ids, 1):
                    if fid in expected_faqs:
                        matched_rank = idx
                        break

            if matched_rank is not None:
                mrr_sum += 1.0 / matched_rank
                if matched_rank <= 1:
                    hit_1 += 1
                if matched_rank <= 3:
                    hit_3 += 1
                if matched_rank <= 5:
                    hit_5 += 1
            else:
                passed = False
                fail_reasons.append(f"Expected FAQ {expected_faqs} not in reranked top-5: {reranked_ids}")

            if expect_grounded and not grounded:
                passed = False
                fail_reasons.append(f"Expected grounded answer, but pipeline abstained (confidence={confidence})")
            elif grounded:
                correct_grounded += 1

            # Check citation correctness
            if expected_faqs:
                citation_match = any(exp in sources for exp in expected_faqs)
                if not citation_match:
                    passed = False
                    fail_reasons.append(f"Citations {sources} do not contain expected {expected_faqs}")

            # Check required keywords in answer
            lower_ans = ans.lower()
            if req_keywords:
                matched_kw = any(kw in lower_ans for kw in req_keywords)
                if not matched_kw:
                    passed = False
                    fail_reasons.append(f"Answer missing required semantic keywords {req_keywords}")

        # Check forbidden keywords (security / leakage)
        if forbid_keywords:
            for fkw in forbid_keywords:
                if fkw.lower() in ans.lower():
                    passed = False
                    fail_reasons.append(f"Forbidden term '{fkw}' leaked in answer")

        if passed:
            category_stats[cat]["pass"] += 1
            status = "PASS"
            reason_str = f"Verified: FAQ {sources[:1]} cited | Grounded={grounded} | Conf={confidence:.3f}"
        else:
            category_stats[cat]["fail"] += 1
            status = "FAIL"
            reason_str = "; ".join(fail_reasons)

        icon = "✅" if passed else "❌"
        print(f"[{icon} {status}] {t_id:10s} | {cat:22s} | {query[:45]:45s} | {reason_str}")

        test_results.append({
            "test_id": t_id,
            "category": cat,
            "query": query,
            "expanded_query": search_q,
            "expected_faqs": expected_faqs,
            "status": status,
            "passed": passed,
            "grounded": grounded,
            "confidence": confidence,
            "sources": sources,
            "latency_ms": round(lat, 2),
            "reasons": fail_reasons,
            "diagnostics": {
                "dense_ids": dense_ids,
                "dense_scores": dense_scores,
                "bm25_ids": bm25_ids,
                "bm25_scores": bm25_scores,
                "hybrid_ids": hybrid_ids,
                "reranked_ids": reranked_ids,
                "reranked_scores": reranked_scores,
            },
            "answer_snippet": ans[:160] + ("..." if len(ans) > 160 else "")
        })

    total_tests = len(SEMANTIC_TEST_CASES)
    total_passed = sum(1 for r in test_results if r["passed"])
    pass_rate = (total_passed / total_tests) * 100.0

    hit1_rate = (hit_1 / answerable_count) * 100.0 if answerable_count > 0 else 0.0
    hit3_rate = (hit_3 / answerable_count) * 100.0 if answerable_count > 0 else 0.0
    hit5_rate = (hit_5 / answerable_count) * 100.0 if answerable_count > 0 else 0.0
    mrr = (mrr_sum / answerable_count) if answerable_count > 0 else 0.0
    grounded_rate = (correct_grounded / answerable_count) * 100.0 if answerable_count > 0 else 0.0
    unans_total = sum(1 for tc in SEMANTIC_TEST_CASES if tc["expect_abstain"])
    abstain_rate = (correct_abstentions / unans_total) * 100.0 if unans_total > 0 else 0.0
    avg_lat = float(np.mean(latencies))

    print("\n" + "=" * 110)
    print(" SEMANTIC AUDIT SUMMARY & RETRIEVAL BENCHMARK")
    print("=" * 110)
    print(f"Total Test Cases:               {total_tests}")
    print(f"Passed:                         {total_passed} / {total_tests} ({pass_rate:.1f}%)")
    print(f"Hit Rate @ 1 (Top-1 Accuracy):  {hit1_rate:.1f}% ({hit_1}/{answerable_count})")
    print(f"Hit Rate @ 3:                   {hit3_rate:.1f}% ({hit_3}/{answerable_count})")
    print(f"Hit Rate @ 5:                   {hit5_rate:.1f}% ({hit_5}/{answerable_count})")
    print(f"MRR (Mean Reciprocal Rank):     {mrr:.3f}")
    print(f"Answer Grounding Rate:          {grounded_rate:.1f}% ({correct_grounded}/{answerable_count})")
    print(f"Unanswerable Abstention Rate:   {abstain_rate:.1f}% ({correct_abstentions}/{unans_total})")
    print(f"Average Pipeline Latency:       {avg_lat:.1f} ms")

    print("\nBreakdown by Category:")
    for cat, stats in category_stats.items():
        pct = (stats["pass"] / stats["total"]) * 100.0 if stats["total"] > 0 else 0.0
        print(f"  • {cat:28s}: {stats['pass']:2d}/{stats['total']:2d} passed ({pct:5.1f}%)")

    # Save results to json
    results_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": total_passed,
                "pass_rate": round(pass_rate, 2),
                "hit_rate_1": round(hit1_rate, 2),
                "hit_rate_3": round(hit3_rate, 2),
                "hit_rate_5": round(hit5_rate, 2),
                "mrr": round(mrr, 3),
                "grounded_rate": round(grounded_rate, 2),
                "abstention_rate": round(abstain_rate, 2),
                "avg_latency_ms": round(avg_lat, 2)
            },
            "category_stats": category_stats,
            "test_cases": test_results
        }, f, indent=2)
    print(f"\nSaved structured evaluation results to: {results_path}")

    # Generate Markdown Report
    report_path = os.path.join(os.path.dirname(__file__), "semantic_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Semantic Retrieval, Paraphrase, and Synonym Evaluation Report\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Semantic Tests Executed:** {total_tests}\n")
        f.write(f"- **Passed:** {total_passed} / {total_tests} (**{pass_rate:.1f}%**)\n")
        f.write(f"- **Hit Rate @ 1 (Top-1 Accuracy):** {hit1_rate:.1f}%\n")
        f.write(f"- **Hit Rate @ 3:** {hit3_rate:.1f}%\n")
        f.write(f"- **Hit Rate @ 5:** {hit5_rate:.1f}%\n")
        f.write(f"- **Mean Reciprocal Rank (MRR):** {mrr:.3f}\n")
        f.write(f"- **Answer Grounding Rate (Answerable Queries):** {grounded_rate:.1f}%\n")
        f.write(f"- **Correct Abstention Rate (Unanswerable Queries):** {abstain_rate:.1f}%\n")
        f.write(f"- **Average Query Latency:** {avg_lat:.1f} ms\n\n")

        f.write("## Category Performance Breakdown\n\n")
        f.write("| Category | Total | Passed | Failed | Pass Rate |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|\n")
        for cat, stats in category_stats.items():
            pct = (stats["pass"] / stats["total"]) * 100.0 if stats["total"] > 0 else 0.0
            f.write(f"| {cat} | {stats['total']} | {stats['pass']} | {stats['fail']} | **{pct:.1f}%** |\n")

        f.write("\n## The 10 Cafeteria & Dining Paraphrases Verification\n\n")
        f.write("| Test ID | User Query | Target FAQ | Top Reranked | Grounded? | Pass? |\n")
        f.write("|:---|:---|:---:|:---:|:---:|:---:|\n")
        for r in test_results:
            if r["category"] == "Cafeteria Paraphrase":
                target = r["expected_faqs"][0]
                top_r = r["diagnostics"]["reranked_ids"][0] if r["diagnostics"]["reranked_ids"] else "None"
                pass_icon = "PASS" if r["passed"] else "FAIL"
                f.write(f"| {r['test_id']} | *\"{r['query']}\"* | `{target}` | `{top_r}` | {r['grounded']} | **{pass_icon}** |\n")

        f.write("\n## Complete Multi-Stage Retrieval Diagnostics\n\n")
        f.write("| ID | Category | Query | Dense Top-3 | BM25 Top-3 | Reranked Top-3 | Citations | Status |\n")
        f.write("|:---|:---|:---|:---|:---|:---|:---|:---:|\n")
        for r in test_results:
            d_top = ", ".join(r["diagnostics"]["dense_ids"][:3])
            b_top = ", ".join(r["diagnostics"]["bm25_ids"][:3])
            r_top = ", ".join(r["diagnostics"]["reranked_ids"][:3])
            cites = ", ".join(r["sources"]) if r["sources"] else "None (Abstained)"
            f.write(f"| {r['test_id']} | {r['category']} | {r['query'][:35]} | {d_top} | {b_top} | {r_top} | {cites} | **{r['status']}** |\n")

    print(f"Saved comprehensive semantic markdown report to: {report_path}")
    return pass_rate == 100.0


if __name__ == "__main__":
    success = run_semantic_evaluation()
    sys.exit(0 if success else 1)
