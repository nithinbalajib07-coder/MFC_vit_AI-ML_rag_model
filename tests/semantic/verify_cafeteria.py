"""
Verify all 11 user-specified cafeteria & dining paraphrase queries against SMU-FAQ-010.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import RAGPipeline

def verify_cafeteria():
    pipeline = RAGPipeline()
    queries = [
        "Where is the cafeteria located?",
        "Where can I get food on campus?",
        "Where is the campus cafeteria?",
        "What dining facilities does the university have?",
        "Where can I buy lunch at SMU?",
        "Is there a place to eat at Saint Mary's?",
        "Where are the food outlets located?",
        "What are the university's dining options?",
        "Where can students grab a meal?",
        "Where can I find the food court?",
        "Where can I buy snacks on campus?"
    ]

    print("=" * 80)
    print(" VERIFYING CAFETERIA & CAMPUS DINING QUERIES (SMU-FAQ-010)")
    print("=" * 80)

    all_passed = True
    for i, q in enumerate(queries, 1):
        res = pipeline.query(q)
        top_faq = res["sources"][0]["faq_id"] if res["sources"] else "None"
        all_faqs = [s["faq_id"] for s in res.get("sources", [])]
        is_grounded = res.get("is_grounded", False)
        conf = res.get("confidence", 0.0)
        has_smu_010 = "SMU-FAQ-010" in all_faqs
        
        passed = has_smu_010 and is_grounded
        if not passed:
            all_passed = False

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{status}] Q{i:02d}: '{q}'")
        print(f"       Top FAQ: {top_faq} (In Sources: {has_smu_010}) | Grounded: {is_grounded} | Confidence: {conf:.1%}")
        answer_preview = res["answer"].replace("\n", " ")[:120]
        print(f"       Answer: {answer_preview}...\n")

    print("=" * 80)
    if all_passed:
        print(" ALL 11 CAFETERIA & DINING PARAPHRASES RETRIEVED SMU-FAQ-010 AND GROUNDED!")
    else:
        print(" SOME CAFETERIA PARAPHRASES FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    verify_cafeteria()
