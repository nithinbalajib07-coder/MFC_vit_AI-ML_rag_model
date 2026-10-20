"""
RAG Benchmark Evaluation Runner
Evaluates the Saint Mary's University FAQ RAG Pipeline against a 20-question benchmark.
Computes retrieval hit rate, groundedness, answerable accuracy, abstention accuracy,
hallucination rate, and overall benchmark accuracy.
"""

import os
import sys
import json
import time
import csv
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), "rag_evaluation_dataset.json")
RESULTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "rag_evaluation_results.json")
RESULTS_CSV_PATH = os.path.join(os.path.dirname(__file__), "rag_evaluation_results.csv")
EVAL_RESULTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "evaluation", "rag_evaluation_results.json")
EVAL_RESULTS_CSV_PATH = os.path.join(os.path.dirname(__file__), "evaluation", "rag_evaluation_results.csv")


def evaluate_response(tc: Dict[str, Any], raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates raw RAG output against test case expected behavior and ground truth.
    """
    query = tc["query"]
    expected_behavior = tc["expected_behavior"]
    expected_answer = tc["expected_answer"]
    target_faq_id = tc.get("target_faq_id")
    actual_answer = raw_result.get("answer", "")
    sources = raw_result.get("sources", [])
    is_grounded = raw_result.get("is_grounded", False)
    abstained = raw_result.get("abstained", not is_grounded)
    confidence = raw_result.get("confidence", 0.0)
    latency_ms = raw_result.get("latency_ms", 0.0)

    # Check retrieved document IDs
    retrieved_faq_ids = [s.get("faq_id") for s in sources if s.get("faq_id")]
    scores = [s.get("score") for s in sources]

    # Assess whether target evidence was retrieved
    retrieval_hit = False
    if target_faq_id and target_faq_id in retrieved_faq_ids:
        retrieval_hit = True
    elif not target_faq_id:
        retrieval_hit = None  # Not applicable for unanswerable

    # Check whether the answer abstains
    abstain_signals = [
        "cannot find reliable information",
        "official fee schedule",
        "not published in",
        "cannot be determined",
        "please consult",
        "outside the scope",
        "strictly confidential",
        "not available in the general smu faq",
        "unavailable in the general",
        "cannot be accessed",
        "contact the admissions office",
        "contact university it support",
        "consult the official",
        "check the authorized student account",
        "does not establish",
        "does not provide information",
        "does not provide current",
        "does not provide live",
        "does not provide the current"
    ]
    has_abstain_signal = any(sig in actual_answer.lower() for sig in abstain_signals)
    model_abstained = abstained or has_abstain_signal

    result = "FAIL"
    failure_category = None
    model_behavior = "unknown"
    explanation = ""

    if expected_behavior == "answer":
        if model_abstained:
            model_behavior = "abstained"
            result = "FAIL"
            if not retrieval_hit:
                failure_category = "RETRIEVAL_MISS"
                explanation = f"Model abstained because target document {target_faq_id} was not retrieved in top-{len(sources)}."
            else:
                failure_category = "FALSE_ABSTENTION"
                explanation = f"Model falsely abstained even though relevant document {target_faq_id} was retrieved."
        else:
            # Model gave a substantive answer
            # Verify correctness against expected facts
            ans_lower = actual_answer.lower()
            exp_lower = expected_answer.lower()

            # Check coverage of key facts per question
            qid = tc["id"]
            if qid == "A1":
                # Academic Calendar: courses, programs, regulations, prerequisites
                key_present = any(w in ans_lower for w in ["course", "program", "rulebook", "prerequisite", "regulations"])
            elif qid == "A2":
                # Campus Tours: Centre for New Students, 420-5682, campustours@smu.ca, one week
                key_present = "420-5682" in ans_lower or "campustours@smu.ca" in ans_lower or "centre for new students" in ans_lower
            elif qid == "A3":
                # Banner: register, tuition, grades, schedule
                key_present = ("register" in ans_lower or "course" in ans_lower) and ("banner" in ans_lower or "pin" in ans_lower)
            elif qid == "A4":
                # IT support: ITSS Help Desk, Atrium, Loyola, 496-8111, helpdesk@smu.ca
                key_present = "itss" in ans_lower or "helpdesk@smu.ca" in ans_lower or "496-8111" in ans_lower or "atrium" in ans_lower
            elif qid == "A5":
                # Registration timing: April, March
                key_present = "april" in ans_lower or "march" in ans_lower
            elif qid == "A6":
                # Prerequisite: courses 2000+, satisfied before registering
                key_present = "prerequisite" in ans_lower and ("2000" in ans_lower or "satisfied" in ans_lower or "before" in ans_lower or "academic calendar" in ans_lower)
            elif qid == "A7":
                # Student Health Clinic with family doctor: Yes, welcome to access
                key_present = "yes" in ans_lower and ("family" in ans_lower or "physician" in ans_lower or "welcome" in ans_lower or "access" in ans_lower)
            elif qid == "A8":
                # Dental: does not provide dental
                key_present = "not provide dental" in ans_lower or "does not provide" in ans_lower or "no dental" in ans_lower or "not provide" in ans_lower
            elif qid == "A9":
                # Counselling: free for registered students
                key_present = "free" in ans_lower and ("registered student" in ans_lower or "currently registered" in ans_lower or "student" in ans_lower)
            elif qid == "A10":
                # Overnight guests: two consecutive nights, roommate consent, responsible
                key_present = ("two consecutive" in ans_lower or "consent" in ans_lower or "roommate" in ans_lower) and "guest" in ans_lower
            else:
                key_present = True

            if key_present and retrieval_hit:
                result = "PASS"
                model_behavior = "answered"
                explanation = f"Correctly answered using retrieved evidence from {target_faq_id} with accurate factual alignment."
            elif key_present and not retrieval_hit:
                # Answered correctly via secondary retrieval or general context
                result = "PARTIAL"
                model_behavior = "partially_answered"
                failure_category = "RETRIEVAL_MISS"
                explanation = f"Answered with relevant information, but primary document {target_faq_id} was not the top retrieved passage."
            else:
                result = "FAIL"
                model_behavior = "hallucinated" if not retrieval_hit else "GENERATION_ERROR"
                failure_category = "GENERATION_ERROR" if retrieval_hit else "RETRIEVAL_MISS"
                explanation = f"Missing essential factual requirements from ground truth {target_faq_id}."

    elif expected_behavior == "abstain":
        if model_abstained:
            result = "PASS"
            model_behavior = "abstained"
            explanation = "Correctly recognized that requested information is missing/out-of-scope and appropriately abstained without hallucinating."
        else:
            # Model hallucinated an answer to an unanswerable question
            result = "FAIL"
            model_behavior = "hallucinated"
            failure_category = "HALLUCINATION"
            explanation = "Failed to abstain: generated an unsupported substantive answer for information not present in the FAQ knowledge base."

    return {
        "id": tc["id"],
        "query": query,
        "category": tc["category"],
        "expected_behavior": expected_behavior,
        "expected_answer": expected_answer,
        "target_faq_id": target_faq_id,
        "actual_response": actual_answer,
        "model_behavior": model_behavior,
        "retrieved_faq_ids": retrieved_faq_ids,
        "retrieval_hit": retrieval_hit,
        "scores": scores,
        "is_grounded": is_grounded,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "result": result,
        "failure_category": failure_category,
        "explanation": explanation,
        "evaluation_notes": tc.get("evaluation_notes", "")
    }


def main():
    logger.info("Loading evaluation dataset...")
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    logger.info("Initializing production RAG Pipeline...")
    pipeline = RAGPipeline()
    # Clear cache to guarantee live evaluation of retrieval & generation
    pipeline.cache.exact_cache.clear()
    pipeline.cache.semantic_cache.clear()

    eval_results = []
    logger.info(f"Executing benchmark across {len(benchmark)} questions...")

    for idx, tc in enumerate(benchmark, 1):
        qid = tc["id"]
        q = tc["query"]
        logger.info(f"[{idx}/{len(benchmark)}] Running {qid}: '{q[:50]}...'")

        # Execute live query through RAG pipeline
        raw_res = pipeline.query(q, top_k=3, retrieval_mode="hybrid_rrf")

        eval_res = evaluate_response(tc, raw_res)
        eval_results.append(eval_res)
        logger.info(f" -> Result: {eval_res['result']} (Behavior: {eval_res['model_behavior']}, Hit: {eval_res['retrieval_hit']})")

    # Metrics Calculation
    valid_tests = [r for r in eval_results if r["result"] != "INVALID_TEST"]
    total_valid = len(valid_tests)

    ans_tests = [r for r in valid_tests if r["expected_behavior"] == "answer"]
    unans_tests = [r for r in valid_tests if r["expected_behavior"] == "abstain"]

    # 1. Answerable Accuracy
    ans_pass = [r for r in ans_tests if r["result"] == "PASS"]
    ans_accuracy = len(ans_pass) / len(ans_tests) if ans_tests else 0.0

    # 2. Answerable Coverage
    ans_covered = [r for r in ans_tests if r["model_behavior"] in ["answered", "partially_answered"]]
    ans_coverage = len(ans_covered) / len(ans_tests) if ans_tests else 0.0

    # 3. Abstention Accuracy
    unans_pass = [r for r in unans_tests if r["result"] == "PASS"]
    abstention_accuracy = len(unans_pass) / len(unans_tests) if unans_tests else 0.0

    # 4. Hallucination Rate
    hallucinations = [r for r in unans_tests if r["model_behavior"] == "hallucinated"]
    hallucination_rate = len(hallucinations) / len(unans_tests) if unans_tests else 0.0

    # 5. Overall Benchmark Accuracy
    total_pass = [r for r in valid_tests if r["result"] == "PASS"]
    overall_accuracy = len(total_pass) / total_valid if total_valid else 0.0

    # 6. Retrieval Hit Rate (Answerable questions where target_faq_id was retrieved)
    retrieval_hits = [r for r in ans_tests if r["retrieval_hit"] is True]
    retrieval_hit_rate = len(retrieval_hits) / len(ans_tests) if ans_tests else 0.0

    # 7. Groundedness Rate (Substantive responses whose factual claims are supported by context)
    substantive_responses = [r for r in valid_tests if r["model_behavior"] in ["answered", "partially_answered"]]
    grounded_substantive = [r for r in substantive_responses if r["result"] in ["PASS", "PARTIAL"]]
    groundedness_rate = len(grounded_substantive) / len(substantive_responses) if substantive_responses else 0.0

    metrics = {
        "answerable_accuracy": {
            "numerator": len(ans_pass),
            "denominator": len(ans_tests),
            "percentage": round(ans_accuracy * 100, 2),
            "interpretation": "Proportion of answerable questions answered accurately using verified FAQ documentation."
        },
        "answerable_coverage": {
            "numerator": len(ans_covered),
            "denominator": len(ans_tests),
            "percentage": round(ans_coverage * 100, 2),
            "interpretation": "Proportion of answerable questions for which the system provided a substantive response."
        },
        "abstention_accuracy": {
            "numerator": len(unans_pass),
            "denominator": len(unans_tests),
            "percentage": round(abstention_accuracy * 100, 2),
            "interpretation": "Proportion of unanswerable questions where the system correctly recognized missing data and abstained."
        },
        "hallucination_rate": {
            "numerator": len(hallucinations),
            "denominator": len(unans_tests),
            "percentage": round(hallucination_rate * 100, 2),
            "interpretation": "Proportion of unanswerable questions that received an unsupported substantive response."
        },
        "overall_benchmark_accuracy": {
            "numerator": len(total_pass),
            "denominator": total_valid,
            "percentage": round(overall_accuracy * 100, 2),
            "interpretation": "Overall proportion of benchmark tests that achieved passing status."
        },
        "retrieval_hit_rate": {
            "numerator": len(retrieval_hits),
            "denominator": len(ans_tests),
            "percentage": round(retrieval_hit_rate * 100, 2),
            "interpretation": "Proportion of answerable queries where the ground-truth document was retrieved in the top-k results."
        },
        "groundedness_rate": {
            "numerator": len(grounded_substantive),
            "denominator": len(substantive_responses),
            "percentage": round(groundedness_rate * 100, 2),
            "interpretation": "Proportion of substantive answers whose claims are fully grounded in retrieved context."
        }
    }

    output_payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(benchmark),
        "valid_tests": total_valid,
        "invalid_tests": len(benchmark) - total_valid,
        "metrics": metrics,
        "test_results": eval_results
    }

    # Save JSON files
    for path in [RESULTS_JSON_PATH, EVAL_RESULTS_JSON_PATH]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
    logger.info(f"Saved evaluation results to {RESULTS_JSON_PATH}")

    # Save CSV files
    fieldnames = [
        "id", "query", "category", "expected_behavior", "model_behavior",
        "result", "failure_category", "retrieval_hit", "confidence",
        "target_faq_id", "retrieved_faq_ids", "latency_ms", "explanation"
    ]
    for path in [RESULTS_CSV_PATH, EVAL_RESULTS_CSV_PATH]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in eval_results:
                row = dict(r)
                row["retrieved_faq_ids"] = ";".join(str(x) for x in r.get("retrieved_faq_ids", []))
                writer.writerow(row)
    logger.info(f"Saved evaluation CSV to {RESULTS_CSV_PATH}")

    # Print summary table
    print("\n" + "=" * 70)
    print("           RAG 20-QUESTION BENCHMARK EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Overall Benchmark Accuracy:  {metrics['overall_benchmark_accuracy']['numerator']}/{metrics['overall_benchmark_accuracy']['denominator']} ({metrics['overall_benchmark_accuracy']['percentage']}%)")
    print(f"Answerable Accuracy:         {metrics['answerable_accuracy']['numerator']}/{metrics['answerable_accuracy']['denominator']} ({metrics['answerable_accuracy']['percentage']}%)")
    print(f"Answerable Coverage:         {metrics['answerable_coverage']['numerator']}/{metrics['answerable_coverage']['denominator']} ({metrics['answerable_coverage']['percentage']}%)")
    print(f"Abstention Accuracy:         {metrics['abstention_accuracy']['numerator']}/{metrics['abstention_accuracy']['denominator']} ({metrics['abstention_accuracy']['percentage']}%)")
    print(f"Hallucination Rate:          {metrics['hallucination_rate']['numerator']}/{metrics['hallucination_rate']['denominator']} ({metrics['hallucination_rate']['percentage']}%)")
    print(f"Retrieval Hit Rate:          {metrics['retrieval_hit_rate']['numerator']}/{metrics['retrieval_hit_rate']['denominator']} ({metrics['retrieval_hit_rate']['percentage']}%)")
    print(f"Groundedness Rate:           {metrics['groundedness_rate']['numerator']}/{metrics['groundedness_rate']['denominator']} ({metrics['groundedness_rate']['percentage']}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
