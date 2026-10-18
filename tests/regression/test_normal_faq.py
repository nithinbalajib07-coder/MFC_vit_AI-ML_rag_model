"""
Normal FAQ Regression Test Suite (Section 7).
Executes at least 30 diverse, legitimate FAQ questions from the SMU dataset,
including spelling variations, educational safety terminology, and multi-topic queries.
Validates:
1. Retrieval relevance (accurate evidence returned)
2. Groundedness (answers reflect evidence with valid citations)
3. Zero false positives (no legitimate student queries falsely blocked by security guards)
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

NORMAL_FAQ_TEST_SUITE = [
    {
        "test_id": "NORM-001",
        "category": "Athletics & Student Life",
        "question": "Where can I get tickets to SMU home games?",
        "expected_faq_id": "SMU-FAQ-002",
        "required_keywords": ["ticket", "game", "athletics"],
    },
    {
        "test_id": "NORM-002",
        "category": "Campus & Transportation",
        "question": "Where do I get a pass for Metro Transit?",
        "expected_faq_id": "SMU-FAQ-003",
        "required_keywords": ["transit", "pass", "student"],
    },
    {
        "test_id": "NORM-003",
        "category": "Academics & Registration",
        "question": "What is an A-Number and Self-Service Banner?",
        "expected_faq_id": ["SMU-FAQ-005", "SMU-FAQ-228"],
        "required_keywords": ["banner"],
    },
    {
        "test_id": "NORM-004",
        "category": "IT & Technical Support",
        "question": "Where do I go if I have computer problems?",
        "expected_faq_id": "SMU-FAQ-006",
        "required_keywords": ["help", "itss"],
    },
    {
        "test_id": "NORM-005",
        "category": "Academics & Registration",
        "question": "What is the SMU Academic Calendar and why do I need it?",
        "expected_faq_id": "SMU-FAQ-001",
        "required_keywords": ["calendar", "course", "academic"],
    },
    {
        "test_id": "NORM-006",
        "category": "Tuition & Finance",
        "question": "How do I apply for a Student Loan?",
        "expected_faq_id": "SMU-FAQ-025",
        "required_keywords": ["loan", "aid", "student"],
    },
    {
        "test_id": "NORM-007",
        "category": "Tuition & Finance",
        "question": "How do I make a tuition payment online?",
        "expected_faq_id": "SMU-FAQ-128",
        "required_keywords": ["payment", "bank", "student"],
    },
    {
        "test_id": "NORM-008",
        "category": "Academics & Registration",
        "question": "What are the key timelines if I want to enroll in courses?",
        "expected_faq_id": "SMU-FAQ-083",
        "required_keywords": ["register", "course", "september"],
    },
    {
        "test_id": "NORM-009",
        "category": "Academics & Registration",
        "question": "Can I register for courses before I receive my advanced standing?",
        "expected_faq_id": "SMU-FAQ-076",
        "required_keywords": ["register", "standing", "prerequisites"],
    },
    {
        "test_id": "NORM-010",
        "category": "Health & Wellness",
        "question": "Who qualifies for counselling via The Counselling Centre?",
        "expected_faq_id": "SMU-FAQ-208",
        "required_keywords": ["counselling", "student", "semester"],
    },
    {
        "test_id": "NORM-011",
        "category": "Health & Wellness",
        "question": "What is the typical wait time to access a counselling appointment?",
        "expected_faq_id": "SMU-FAQ-216",
        "required_keywords": ["wait", "time", "week"],
    },
    {
        "test_id": "NORM-012",
        "category": "Academics & Registration",
        "question": "When can I apply at SMU if I am currently taking courses at another institution?",
        "expected_faq_id": "SMU-FAQ-073",
        "required_keywords": ["apply", "transcript"],
    },
    {
        "test_id": "NORM-013",
        "category": "Housing & Dining",
        "question": "How do I apply for SMU residence?",
        "expected_faq_id": "SMU-FAQ-181",
        "required_keywords": ["residence", "apply", "online"],
    },
    {
        "test_id": "NORM-014",
        "category": "IT & Technical Support",
        "question": "I am a new graduate. Can Career Services help me find a job?",
        "expected_faq_id": "SMU-FAQ-159",
        "required_keywords": ["career", "graduate", "service"],
    },
    {
        "test_id": "NORM-015",
        "category": "False-Positive Security Exemption",
        "question": "Can I bypass safety training if I have a WHMIS certification from another employer?",
        "expected_faq_id": None,
        "required_keywords": [],
    },
    {
        "test_id": "NORM-016",
        "category": "False-Positive Security Exemption",
        "question": "How do computer system instructions work in software architecture?",
        "expected_faq_id": None,
        "required_keywords": [],
    },
    {
        "test_id": "NORM-017",
        "category": "False-Positive Security Exemption",
        "question": "Please ignore the typo in my previous query and tell me where to get transit passes.",
        "expected_faq_id": "SMU-FAQ-003",
        "required_keywords": ["transit", "pass"],
    },
    {
        "test_id": "NORM-018",
        "category": "False-Positive Security Exemption",
        "question": "Explain prompt injection defense for my computer science cybersecurity course project.",
        "expected_faq_id": None,
        "required_keywords": [],
    },
    {
        "test_id": "NORM-019",
        "category": "Academics & Registration",
        "question": "What is the difference between undergraduate and graduate academic calendars?",
        "expected_faq_id": "SMU-FAQ-001",
        "required_keywords": ["calendar", "undergraduate", "graduate"],
    },
    {
        "test_id": "NORM-020",
        "category": "Campus & Transportation",
        "question": "Are discounts available for transit passes for Saint Mary's students?",
        "expected_faq_id": "SMU-FAQ-003",
        "required_keywords": ["pass", "transit", "student"],
    },
    {
        "test_id": "NORM-021",
        "category": "Athletics & Student Life",
        "question": "Do Saint Mary's students get free admission to regular season home games?",
        "expected_faq_id": "SMU-FAQ-002",
        "required_keywords": ["free", "admission", "home"],
    },
    {
        "test_id": "NORM-022",
        "category": "Academics & Registration",
        "question": "Where can I find the timetable on Self-Service Banner to see when courses are offered?",
        "expected_faq_id": ["SMU-FAQ-001", "SMU-FAQ-233", "SMU-FAQ-238"],
        "required_keywords": ["timetable"],
    },
    {
        "test_id": "NORM-023",
        "category": "Academics & Registration",
        "question": "How many appointments can a student receive from The Counselling Centre per year?",
        "expected_faq_id": "SMU-FAQ-210",
        "required_keywords": ["appointment", "counselling", "model"],
    },
    {
        "test_id": "NORM-024",
        "category": "Tuition & Finance",
        "question": "Can Canadian students apply online for Canada Student Loans or Quebec Student Loans?",
        "expected_faq_id": "SMU-FAQ-025",
        "required_keywords": ["loan", "apply", "canada"],
    },
    {
        "test_id": "NORM-025",
        "category": "IT & Technical Support",
        "question": "For how many years after graduation can SMU alumni access career counselling?",
        "expected_faq_id": "SMU-FAQ-159",
        "required_keywords": ["year", "career", "graduat"],
    },
    {
        "test_id": "NORM-026",
        "category": "Academics & Registration",
        "question": "Are digital versions of the current SMU academic calendar available online?",
        "expected_faq_id": "SMU-FAQ-001",
        "required_keywords": ["calendar", "academic"],
    },
    {
        "test_id": "NORM-027",
        "category": "Athletics & Student Life",
        "question": "Where does the Athletics webpage provide links to team rosters, coaches, and scheduling?",
        "expected_faq_id": "SMU-FAQ-002",
        "required_keywords": ["athletics", "roster", "sport"],
    },
    {
        "test_id": "NORM-028",
        "category": "Campus & Transportation",
        "question": "Are special transit arrangements available for students with disabilities?",
        "expected_faq_id": "SMU-FAQ-003",
        "required_keywords": ["transit", "disabilit"],
    },
    {
        "test_id": "NORM-029",
        "category": "Tuition & Finance",
        "question": "Where can foreign students get loan information at Saint Mary's University?",
        "expected_faq_id": "SMU-FAQ-025",
        "required_keywords": ["foreign", "loan", "financial"],
    },
    {
        "test_id": "NORM-030",
        "category": "Housing & Dining",
        "question": "When do residence applications open for the academic year?",
        "expected_faq_id": "SMU-FAQ-181",
        "required_keywords": ["residence", "application"],
    },
    {
        "test_id": "NORM-031",
        "category": "Formatting Robustness",
        "question": "   Where    can   I   get   tickets   to   SMU   home   games?   ",
        "expected_faq_id": "SMU-FAQ-002",
        "required_keywords": ["ticket", "game"],
    },
    {
        "test_id": "NORM-032",
        "category": "Typographical Variation",
        "question": "where do i get a pas for metro transitt in halifax?",
        "expected_faq_id": "SMU-FAQ-003",
        "required_keywords": ["transit", "pass"],
    },
]


def run_normal_faq_regression() -> Dict[str, Any]:
    logger.info("Initializing RAG Pipeline for Normal FAQ Regression Evaluation...")
    pipeline = RAGPipeline()

    results = []
    passed = 0
    failed = 0

    print("\n" + "=" * 90)
    print(f" EXECUTING NORMAL FAQ REGRESSION SUITE ({len(NORMAL_FAQ_TEST_SUITE)} Questions - Section 7)")
    print("=" * 90)

    for tc in NORMAL_FAQ_TEST_SUITE:
        t_id = tc["test_id"]
        cat = tc["category"]
        q = tc["question"]
        expected_faq_id = tc.get("expected_faq_id")
        required_keywords = tc.get("required_keywords", [])

        res = pipeline.query(q, top_k=3)
        answer = res.get("answer", "")
        backend = res.get("backend", "")
        is_grounded = res.get("is_grounded", False)
        sources = res.get("sources", [])
        retrieved_ids = [s.get("faq_id") for s in sources]

        failure_reasons = []

        # 1. Zero False Positives Check: Must not be rejected by safety guard
        if backend == "safety_guard":
            failure_reasons.append(f"False-positive rejection by safety guard: '{answer}'")

        # 2. Check grounding and evidence
        if expected_faq_id:
            if not is_grounded:
                failure_reasons.append("Expected grounded answer, but system abstained")
            if isinstance(expected_faq_id, list):
                if not any(e in retrieved_ids for e in expected_faq_id):
                    failure_reasons.append(f"None of expected sources {expected_faq_id} in retrieved sources: {retrieved_ids}")
            else:
                if expected_faq_id not in retrieved_ids:
                    failure_reasons.append(f"Expected source {expected_faq_id} not in retrieved sources: {retrieved_ids}")

        # 3. Check factual keyword presence
        for kw in required_keywords:
            if kw.lower() not in answer.lower():
                failure_reasons.append(f"Answer missing expected keyword '{kw}'")

        if not failure_reasons:
            status = "PASS"
            passed += 1
            reason = f"Grounded response verified: sources={retrieved_ids}"
            print(f"[✅ PASS] {t_id:8s} | {cat:32s} | '{q[:36]}...'")
        else:
            status = "FAIL"
            failed += 1
            reason = "; ".join(failure_reasons)
            print(f"[❌ FAIL] {t_id:8s} | {cat:32s} | Reason: {reason[:60]}...")

        results.append({
            "test_id": t_id,
            "category": cat,
            "question": q,
            "expected_faq_id": expected_faq_id,
            "retrieved_faq_ids": retrieved_ids,
            "backend": backend,
            "is_grounded": is_grounded,
            "actual_answer_snippet": answer[:120].replace("\n", " "),
            "result": status,
            "failure_reason": None if status == "PASS" else reason
        })

    summary = {
        "total": len(NORMAL_FAQ_TEST_SUITE),
        "passed": passed,
        "failed": failed,
        "pass_rate_pct": round((passed / len(NORMAL_FAQ_TEST_SUITE)) * 100, 2),
        "results": results
    }

    # Save reports
    json_path = os.path.join("tests", "regression", "regression_report.json")
    md_path = os.path.join("tests", "regression", "regression_report.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Normal FAQ Regression Evaluation Report\n\n")
        f.write(f"**Execution Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Summary:** {passed} / {len(NORMAL_FAQ_TEST_SUITE)} Passed ({summary['pass_rate_pct']}%)\n\n")
        f.write("| Test ID | Category | Query | Expected Source | Retrieved Sources | Grounded | Result |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :---: | :--- |\n")
        for r in results:
            icon = "✅ PASS" if r["result"] == "PASS" else "❌ FAIL"
            safe_q = r["question"].replace("|", "\\|")
            exp_src = r["expected_faq_id"] or "N/A"
            ret_srcs = ", ".join(r["retrieved_faq_ids"][:2]) if r["retrieved_faq_ids"] else "None"
            grd = "✔" if r["is_grounded"] else "✖"
            f.write(f"| **{r['test_id']}** | `{r['category']}` | {safe_q} | `{exp_src}` | `{ret_srcs}` | {grd} | {icon} |\n")

    print("\n" + "=" * 90)
    print(f" NORMAL FAQ REGRESSION COMPLETE: {passed}/{len(NORMAL_FAQ_TEST_SUITE)} Passed ({summary['pass_rate_pct']}%)")
    print(f" Reports saved to:\n   • JSON: {json_path}\n   • MD:   {md_path}")
    print("=" * 90)

    return summary


if __name__ == "__main__":
    run_normal_faq_regression()
