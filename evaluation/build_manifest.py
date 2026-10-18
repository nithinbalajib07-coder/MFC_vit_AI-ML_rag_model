"""
Consolidates all test suites into a single normalized evaluation manifest
matching the exact schema specified in Section 3 & Section 12.
Outputs:
- evaluation/evaluation_manifest.json
- evaluation/evaluation_manifest.csv
"""

import os
import json
import csv
from typing import List, Dict, Any

MANIFEST_JSON = "evaluation/evaluation_manifest.json"
MANIFEST_CSV = "evaluation/evaluation_manifest.csv"

def build_normalized_manifest():
    manifest_records = []

    # 1. Unanswerable Tests (40 questions: U01 - U40)
    unans_path = "tests/unanswerable/unanswerable_report.json"
    if os.path.exists(unans_path):
        with open(unans_path, "r", encoding="utf-8") as f:
            unans_data = json.load(f)
        for r in unans_data.get("results", []):
            sources = r.get("sources", [])
            retrieved_chunks = [s.get("document_id") or s.get("faq_id") for s in sources]
            citations = [s.get("faq_id") for s in sources]
            manifest_records.append({
                "test_id": r.get("test_id"),
                "category": f"Unanswerable - {r.get('category')}",
                "input_question": r.get("input_question"),
                "expected_behavior": r.get("expected_behavior"),
                "expected_answerable": False,
                "expected_security_action": "abstain_or_refuse",
                "required_evidence": "none",
                "citation_required": False,
                "severity": "HIGH",
                "source_fixture": "tests/unanswerable/test_cases.py",
                "actual_output": r.get("actual_answer", ""),
                "retrieved_chunks": retrieved_chunks,
                "actual_citations": citations,
                "result": r.get("result", "PASS"),
                "failure_reason": r.get("failure_reason") or ""
            })

    # 2. Security Audit Tests (44 tests)
    sec_path = "tests/security/security_audit_report.json"
    if os.path.exists(sec_path):
        with open(sec_path, "r", encoding="utf-8") as f:
            sec_data = json.load(f)
        for r in sec_data.get("test_results", []):
            status = r.get("status", "PASS")
            manifest_records.append({
                "test_id": r.get("test_id"),
                "category": f"Security - {r.get('category')}",
                "input_question": r.get("input"),
                "expected_behavior": f"{r.get('expected_guard_behavior')} | {r.get('expected_response_behavior')}",
                "expected_answerable": False if "injection" in r.get("category", "") or "secret" in r.get("category", "") else True,
                "expected_security_action": r.get("expected_guard_behavior"),
                "required_evidence": "isolated_canary" if "secret" in r.get("category", "") else "none",
                "citation_required": False,
                "severity": "CRITICAL" if "leakage" in r.get("category", "") or "direct" in r.get("category", "") else "HIGH",
                "source_fixture": "tests/security/test_cases.py",
                "actual_output": r.get("actual_response_behavior", ""),
                "retrieved_chunks": [r.get("actual_retrieval_behavior", "")],
                "actual_citations": [],
                "result": status,
                "failure_reason": r.get("failure_reason") or ""
            })

    # 3. Normal FAQ Regression Tests (32 questions)
    reg_path = "tests/regression/regression_report.json"
    if os.path.exists(reg_path):
        with open(reg_path, "r", encoding="utf-8") as f:
            reg_data = json.load(f)
        for r in reg_data.get("results", []):
            manifest_records.append({
                "test_id": r.get("test_id"),
                "category": f"Regression - {r.get('category')}",
                "input_question": r.get("question"),
                "expected_behavior": "Provide grounded answer with official citations" if r.get("expected_faq_id") else "Abstain safely without false-positive rejection",
                "expected_answerable": bool(r.get("expected_faq_id")),
                "expected_security_action": "allow_safe" if r.get("expected_faq_id") else "abstain_or_refuse",
                "required_evidence": str(r.get("expected_faq_id")),
                "citation_required": bool(r.get("expected_faq_id")),
                "severity": "MEDIUM",
                "source_fixture": "tests/regression/test_normal_faq.py",
                "actual_output": r.get("actual_answer_snippet", ""),
                "retrieved_chunks": r.get("retrieved_faq_ids", []),
                "actual_citations": r.get("retrieved_faq_ids", []) if r.get("is_grounded") else [],
                "result": r.get("result", "PASS"),
                "failure_reason": r.get("failure_reason") or ""
            })

    # 4. Standardized Edge-Case Matrix (50 tests)
    edge_path = "tests/edge_cases/results.json"
    if os.path.exists(edge_path):
        with open(edge_path, "r", encoding="utf-8") as f:
            edge_data = json.load(f)
        edge_list = edge_data if isinstance(edge_data, list) else edge_data.get("results", [])
        for r in edge_list:
            manifest_records.append({
                "test_id": r.get("test_id"),
                "category": f"EdgeCase - {r.get('category')}",
                "input_question": r.get("input") or r.get("name") or "",
                "expected_behavior": r.get("expected_output") or r.get("expected_outcome") or "",
                "expected_answerable": "GROUNDED" in str(r.get("expected_output", "")).upper(),
                "expected_security_action": "; ".join(r.get("security_invariants", [])) if r.get("security_invariants") else "standard_guard",
                "required_evidence": str(r.get("expected_source_ids", [])),
                "citation_required": bool(r.get("expected_source_ids")),
                "severity": "HIGH",
                "source_fixture": "tests/edge_cases/test_definitions.json",
                "actual_output": str(r.get("actual_output") or "")[:150],
                "retrieved_chunks": [],
                "actual_citations": [],
                "result": r.get("status", "PASS"),
                "failure_reason": r.get("failure_reason") or ""
            })

    # 5. Six Core Requirements Suite (HR, RR, AF, PI, CA)
    six_req_path = "tests/six_requirements/results.json"
    if os.path.exists(six_req_path):
        with open(six_req_path, "r", encoding="utf-8") as f:
            six_data = json.load(f)
        for cat_key, cat_records in six_data.items():
            if not isinstance(cat_records, list):
                continue
            for r in cat_records:
                manifest_records.append({
                    "test_id": r.get("test_id"),
                    "category": f"SixRequirements - {cat_key}",
                    "input_question": r.get("query") or r.get("name") or "",
                    "expected_behavior": r.get("name") or "",
                    "expected_answerable": "AF" in r.get("test_id", "") or "HR" in r.get("test_id", ""),
                    "expected_security_action": "pass_criteria_verified",
                    "required_evidence": str(r.get("expected_source") or r.get("expected_top") or ""),
                    "citation_required": bool(r.get("expected_source")),
                    "severity": "CRITICAL" if "PI" in r.get("test_id", "") else "HIGH",
                    "source_fixture": "tests/six_requirements/test_cases.py",
                    "actual_output": r.get("reason") or "",
                    "retrieved_chunks": r.get("retrieved_sources") or ([r.get("actual_top")] if r.get("actual_top") else []),
                    "actual_citations": r.get("retrieved_sources") or ([r.get("actual_top")] if r.get("actual_top") else []),
                    "result": r.get("status", "PASS"),
                    "failure_reason": r.get("reason") if r.get("status") == "FAIL" else ""
                })

    # 6. Semantic Retrieval Audit Suite (40 tests: SEM-CAF-01 to SEM-SEC-03)
    sem_path = "tests/semantic/results.json"
    if os.path.exists(sem_path):
        with open(sem_path, "r", encoding="utf-8") as f:
            sem_data = json.load(f)
        for r in sem_data.get("test_cases", []):
            is_unans = "Unanswerable" in r.get("category", "") or "Security" in r.get("category", "")
            manifest_records.append({
                "test_id": r.get("test_id"),
                "category": f"Semantic - {r.get('category')}",
                "input_question": r.get("query"),
                "expected_behavior": f"Retrieve {r.get('expected_faqs')} and generate grounded answer" if not is_unans else "Abstain safely without false answer or injection leakage",
                "expected_answerable": not is_unans,
                "expected_security_action": "abstain_or_refuse" if is_unans else "allow_safe",
                "required_evidence": str(r.get("expected_faqs", [])),
                "citation_required": not is_unans,
                "severity": "CRITICAL" if "Security" in r.get("category", "") else "HIGH",
                "source_fixture": "tests/semantic/test_cases.py",
                "actual_output": f"Confidence: {r.get('confidence')} | Grounded: {r.get('grounded')}",
                "retrieved_chunks": r.get("sources", []),
                "actual_citations": r.get("sources", []),
                "result": r.get("status", "PASS"),
                "failure_reason": "; ".join(r.get("reasons", []))
            })

    # 7. Comprehensive 10-Domain Semantic Evaluation Suite (182 tests)
    domain_sem_path = "evaluation/semantic_test_results.csv"
    if os.path.exists(domain_sem_path):
        with open(domain_sem_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                is_unans = r.get("expected_answerable") == "False"
                manifest_records.append({
                    "test_id": r.get("test_id"),
                    "category": f"DomainSemantic - {r.get('domain')} / {r.get('subdomain')}",
                    "input_question": r.get("test_query"),
                    "expected_behavior": f"Retrieve {r.get('expected_relevant_faq_ids')} with citations" if not is_unans else "Abstain safely without false answer",
                    "expected_answerable": not is_unans,
                    "expected_security_action": "abstain_or_refuse" if is_unans else "allow_safe",
                    "required_evidence": r.get("expected_relevant_faq_ids", ""),
                    "citation_required": not is_unans,
                    "severity": "HIGH",
                    "source_fixture": "evaluation/semantic_tests.jsonl",
                    "actual_output": r.get("final_answer", "")[:150],
                    "retrieved_chunks": [r.get("rerank_top_faq_id", "")],
                    "actual_citations": [c for c in r.get("citations", "").split(";") if c],
                    "result": "PASS" if r.get("passed") == "True" else "FAIL",
                    "failure_reason": r.get("failure_notes") or ""
                })

    os.makedirs(os.path.dirname(MANIFEST_JSON), exist_ok=True)

    # Save JSON manifest
    with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "total_records": len(manifest_records),
            "manifest_version": "2.0.0",
            "records": manifest_records
        }, f, indent=2)

    # Save CSV manifest
    fieldnames = [
        "test_id", "category", "input_question", "expected_behavior",
        "expected_answerable", "expected_security_action", "required_evidence",
        "citation_required", "severity", "source_fixture", "actual_output",
        "retrieved_chunks", "actual_citations", "result", "failure_reason"
    ]
    with open(MANIFEST_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in manifest_records:
            clean_rec = dict(rec)
            clean_rec["retrieved_chunks"] = "; ".join(map(str, clean_rec["retrieved_chunks"]))
            clean_rec["actual_citations"] = "; ".join(map(str, clean_rec["actual_citations"]))
            writer.writerow(clean_rec)

    print(f"Normalized Manifest Generated:")
    print(f"  • Total Test Records: {len(manifest_records)}")
    print(f"  • JSON: {MANIFEST_JSON}")
    print(f"  • CSV:  {MANIFEST_CSV}")

if __name__ == "__main__":
    build_normalized_manifest()
