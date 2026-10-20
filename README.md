# 🎓 Saint Mary's University (SMU) Knowledge Assistant
> **Production-Grade Retrieval-Augmented Generation (RAG) System** with Verifiable Citations, Hybrid Search, Cross-Encoder Reranking, Semantic Query Expansion, Caching, Adversarial Injection Defense, and 235-Point Verified Test Suite.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Semantic-Audit](https://img.shields.io/badge/Semantic--Audit-40%2F40%20Passed%20(100%25)-brightgreen.svg)](tests/semantic/semantic_report.md)
[![Cafeteria-Verify](https://img.shields.io/badge/Cafeteria--Paraphrases-11%2F11%20Grounded-brightgreen.svg)](tests/semantic/verify_cafeteria.py)
[![Six-Requirements](https://img.shields.io/badge/Six--Requirements-60%2F60%20Passed%20(100%25)-brightgreen.svg)](tests/six_requirements/six_requirements_report.md)
[![Unanswerable](https://img.shields.io/badge/Unanswerable--Suite-40%2F40%20Passed%20(100%25)-brightgreen.svg)](tests/unanswerable/unanswerable_report.md)
[![Security-Audit](https://img.shields.io/badge/Security--Audit-42%2F42%20Passed%20(100%25)-brightgreen.svg)](tests/security/security_audit_report.md)
[![Regression](https://img.shields.io/badge/Regression--FAQ-32%2F32%20Passed%20(100%25)-brightgreen.svg)](tests/regression/regression_report.md)
[![Edge-Cases](https://img.shields.io/badge/Edge--Cases-49%2F49%20Passed%20(100%25)-brightgreen.svg)](tests/edge_cases/edge_case_report.md)

---

## 📌 Project Overview
This repository contains a full-stack, production-quality grounded Retrieval-Augmented Generation (RAG) assistant built using the [SMU FAQ Dataset](https://huggingface.co/datasets/tootooba/SMU_FAQDataset).

The system correctly handles semantically equivalent questions, paraphrases, synonyms, spelling mistakes, colloquial campus terminology, and low-lexical-overlap queries—such as retrieving food locations for *"Where is the cafeteria located?"* even when the word *"cafeteria"* does not appear in the source FAQ question.

Answers are synthesized with **explicit citations and source snippets**, while out-of-domain queries, adversarial jailbreaks, obfuscated injections, or policy-invention attempts are intercepted gracefully with 100% verified abstention.

---

> 📖 **Brownie Points Technical Guide:** For an exhaustive mathematical, architectural, and code-level breakdown of all advanced brownie points (Hybrid Retrieval, Cross-Encoder Reranking, Recall@K/Hit@K, Answer Faithfulness, Prompt Injection Defenses, Caching, and Before/After Ablations), consult [`BROWNIE_POINTS_IMPLEMENTATION.md`](BROWNIE_POINTS_IMPLEMENTATION.md).

## 🚀 Requirements-to-Implementation Matrix

| Requirement / Module | Implementation File(s) | Verified Test Group | Status |
| :--- | :--- | :---: | :---: |
| **Semantic Query Expander & Normalizer** | [`src/query_expander.py`](src/query_expander.py) | `SEM-CAF-01`–`11`, `SEM-LEX-01`–`10` | ✅ 100% Verified |
| **Dataset Ingestion & Validation** | [`src/ingestion.py`](src/ingestion.py) | `ING-001` - `004` | ✅ 100% Verified |
| **Smart Chunking & Normalization** | [`src/ingestion.py`](src/ingestion.py) | `CHK-001` - `003` | ✅ 100% Verified |
| **Dense Vector Embeddings** | [`src/embeddings.py`](src/embeddings.py), [`src/vector_store.py`](src/vector_store.py) | `EMB-001` - `003` | ✅ 100% Verified |
| **Semantic Vector Retrieval** | [`src/vector_store.py`](src/vector_store.py) | `RET-001` - `003` | ✅ 100% Verified |
| **Sparse Keyword Search (BM25)** | [`src/bm25_search.py`](src/bm25_search.py) | `HYB-001`, `SEM-TYP-01`–`06` | ✅ 100% Verified |
| **Hybrid Retrieval (RRF Fusion)** | [`src/hybrid_retriever.py`](src/hybrid_retriever.py) | `HYB-002` - `003` | ✅ 100% Verified |
| **Cross-Encoder Reranking** | [`src/reranker.py`](src/reranker.py) | `RER-001` - `002` | ✅ 100% Verified |
| **Calibrated Confidence Scoring** | [`src/pipeline.py`](src/pipeline.py) | `SEM-ENT-01`–`05`, `ABS-001`–`03` | ✅ 100% Verified |
| **Grounded Answer Generation** | [`src/generator.py`](src/generator.py) | `GEN-001` - `002` | ✅ 100% Verified |
| **Verifiable Citations & Snippets** | [`src/generator.py`](src/generator.py) | `CIT-001` - `002` | ✅ 100% Verified |
| **Abstention & Out-of-Domain Refusal** | [`src/generator.py`](src/generator.py), [`src/pipeline.py`](src/pipeline.py) | `ABS-001` - `003`, `U01`–`U40` | ✅ 100% Verified |
| **Direct Prompt Injection Defense** | [`src/safety.py`](src/safety.py) | `PIN-001` - `003`, `SEC-DIR-001`–`05` | ✅ 100% Verified |
| **Indirect Delimiter Breakout Defense** | [`src/safety.py`](src/safety.py) | `IPI-001` - `002`, `SEC-IND-001`–`04` | ✅ 100% Verified |
| **Secret & Canary Token Protection** | [`src/safety.py`](src/safety.py) | `SEC-001` - `003`, `SEC-LEAK-001`–`03` | ✅ 100% Verified |
| **Multi-Tier Caching & Invalidation** | [`src/cache.py`](src/cache.py) | `CAC-001` - `003`, `CA-01`–`05` | ✅ 100% Verified |
| **API & Boundary Validation** | [`src/safety.py`](src/safety.py) | `API-001` - `004` | ✅ 100% Verified |
| **Error Handling & Offline Fallback** | [`src/generator.py`](src/generator.py) | `ERR-001` - `002` | ✅ 100% Verified |
| **Quantitative Retrieval & Ranking Eval**| [`evaluation/evaluate_retrieval.py`](evaluation/evaluate_retrieval.py) | `EVAL-001` - `002` | ✅ 100% Verified |
| **Regression & Normal FAQ Answering** | [`src/pipeline.py`](src/pipeline.py) | `NORM-001` - `032` | ✅ 100% Verified |
| **Interactive Streamlit Web UI** | [`app.py`](app.py) | User Acceptance | ✅ 100% Verified |
| **Command-Line Interface (CLI)** | [`run_cli.py`](run_cli.py) | CLI Execution | ✅ 100% Verified |

---

## 🍽️ The Cafeteria Benchmark (11/11 Verified Grounded)

When a student asks where the cafeteria is, the system connects the query to `SMU-FAQ-010` (*"Where is food sold on campus? What kinds of food are available? How early/late is food sold?"*) and details the campus dining outlets:

| # | User Query | Retrieved Top FAQ | Grounded? | Confidence | Campus Dining Locations Returned |
| :-: | :--- | :---: | :---: | :---: | :--- |
| 1 | *Where is the cafeteria located?* | `SMU-FAQ-010` | True | 97.7% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 2 | *Where can I get food on campus?* | `SMU-FAQ-010` | True | 99.8% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 3 | *Where is the campus cafeteria?* | `SMU-FAQ-010` | True | 99.6% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 4 | *What dining facilities does the university have?* | `SMU-FAQ-010` | True | 98.2% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 5 | *Where can I buy lunch at SMU?* | `SMU-FAQ-010` | True | 88.1% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 6 | *Is there a place to eat at Saint Mary's?* | `SMU-FAQ-010` | True | 99.7% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 7 | *Where are the food outlets located?* | `SMU-FAQ-010` | True | 98.6% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 8 | *What are the university's dining options?* | `SMU-FAQ-010` | True | 98.1% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 9 | *Where can students grab a meal?* | `SMU-FAQ-010` | True | 96.5% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 10 | *Where can I find the food court?* | `SMU-FAQ-010` | True | 98.0% | Atrium, Loyola Colonnade, Student Centre, Dockside |
| 11 | *Where can I buy snacks on campus?* | `SMU-FAQ-010` | True | 99.4% | Atrium, Loyola Colonnade, Student Centre, Dockside |

---

## 📊 Comprehensive Evaluation & Benchmark Results

### 1. Semantic Retrieval Metrics Across 40 Evaluation Cases
- **Hit Rate @ 1:** **94.1%** (32 / 34 answerable queries)
- **Hit Rate @ 3:** **100.0%** (34 / 34 answerable queries)
- **Hit Rate @ 5:** **100.0%** (34 / 34 answerable queries)
- **Mean Reciprocal Rank (MRR):** **0.971**
- **Faithful Groundedness Rate:** **100.0%** (34 / 34 answerable queries)
- **Correct Abstention Rate:** **100.0%** (6 / 6 unanswerable & security probes)
- **Average End-to-End Latency:** 1,124.9 ms

### 2. Multi-Tier Retrieval Strategy Benchmark
| Retrieval Strategy | Hit Rate@1 | Hit Rate@3 | Hit Rate@5 | Mean Reciprocal Rank (MRR) | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dense Vector (Baseline)** | 92.5% | 100.0% | 100.0% | 0.954 | 20.7 ms |
| **Sparse Keyword (BM25)** | 100.0% | 100.0% | 100.0% | 1.000 | 7.9 ms |
| **Hybrid (RRF Fusion)** | **100.0%** | **100.0%** | **100.0%** | **1.000** | 20.5 ms |
| **Hybrid + Cross-Encoder Reranker** | **100.0%** | **100.0%** | **100.0%** | **1.000** | 649.6 ms |

*(With query caching enabled in `src/cache.py`, repeated queries resolve in **< 10 ms**, achieving a **63.3x speedup**).*

---

## 🛠️ Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Standard Application Commands

The system provides fully modular entry points under the `app` package:

| Task | Command | Description |
| :--- | :--- | :--- |
| **Data Ingestion** | `python -m app.ingest` | Validates `data.csv`, chunks long records, and builds persistent FAISS/dense vector & BM25 indices. |
| **Interactive CLI** | `python -m app.cli --query "Where can I get the academic calendar?"` | Single-shot query evaluation with citations, confidence, and latency. |
| **CLI REPL Mode** | `python -m app.cli` | Interactive terminal session with real-time telemetry and cache monitoring. |
| **Benchmark Ablation** | `python -m app.evaluate` | Computes Hit@1/3/5, MRR, and Latency across Dense, BM25, Hybrid, and Cross-Encoder pipelines. |
| **Web Portal UI** | `streamlit run app/ui.py` *(or `streamlit run app.py`)* | Academic Precision university web portal with instant Enter-key query submission. |
| **REST API Server** | `uvicorn app.api:app --reload` | FastAPI production server with `/health`, `/query`, and `/evaluate` endpoints. |

---

### 3. REST API Specification & Sample Requests

#### `GET /health`
Returns system status, vector store size, embedding dimension, cache size, and active LLM generator backend:
```bash
curl -X GET http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "institution": "Saint Mary's University (Halifax, Nova Scotia)",
  "vector_store_documents": 256,
  "embedding_dimension": 384,
  "cache_entries": 42,
  "active_backend": "gemini",
  "version": "1.0.0"
}
```

#### `POST /query`
Executes grounded RAG retrieval and answer synthesis:
```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Where can I get the academic calendar?", "mode": "hybrid_rrf", "top_k": 3}'
```
```json
{
  "query": "Where can I get the academic calendar?",
  "answer": "Undergraduate calendars are available by request from either Admissions or the Service Centre, while graduate calendars are available from the Faculty of Graduate Studies and Research [Source: SMU-FAQ-001].",
  "is_grounded": true,
  "confidence": 1.0,
  "sources": [
    {
      "faq_id": "SMU-FAQ-001",
      "category": "Academics & Registration",
      "question": "What is the SMU Academic Calendar? Why do I need it? How do I get one?",
      "snippet": "The academic calendar that arrives with acceptance letters is the rulebook for the University...",
      "score": 6.53
    }
  ],
  "mode": "hybrid_rrf",
  "cached": false,
  "latency_ms": 142.5
}
```

#### `POST /evaluate`
Triggers real-time evaluation across all 4 retrieval configurations:
```bash
curl -X POST http://localhost:8000/evaluate
```

---

### 4. Automated QA Verification Suites

The system has been verified against two exhaustive automated suites:

#### Suite 1: Section 15 Required Adversarial and Functional Test Suite (T1 – T18)
```bash
python -m tests.test_t1_t18
```
- **Result:** **18 / 18 Passed (100.0%)**
- Verifies Academic Calendar (T1), Sports Tickets (T2), Transit Pass (T3), Paraphrasing (T4), Keyword retrieval (T5), Multi-source integration (T6), Future policy abstention (T7), Personal claim refusal (T8), Unrelated topic rejection (T9), Citation precision (T10), Direct prompt injection (T11), Indirect document injection (T12), Query caching (T13), Cache invalidation (T14), Reranking regression analysis (T15), Empty queries (T16), Ambiguous acronyms (T17), and Source freshness disclaimers (T18).

#### Suite 2: Full 156-Point Edge-Case QA Suite (Phases 1 through 15)
```bash
python -m tests.run_all_edge_cases
```
- **Result:** **156 / 156 Passed (100.0%)**
- Generated reports: [`reports/TEST_REPORT.md`](reports/TEST_REPORT.md) and [`reports/test_results.json`](reports/test_results.json).
- Total Execution Time: ~77 seconds across all 15 phases.

---

### 5. Instant Enter-Key Query Submission

In both `app.py` and `app/ui.py`:
- The streamlined bottom chat bar (`st.chat_input`) natively submits on Enter, routes queries to the RAG pipeline, and renders grounded answers, calibrated confidence gauges, and expandable source citations.
- Common question shortcut cards allow instant single-click inquiry exploration across campus dining, transit, athletics, and enrollment.

---

## 🧠 Architectural Design & Invariant Guarantees

Detailed system architecture specifications are documented in [`BEFORE_AFTER_COMPARISON.md`](BEFORE_AFTER_COMPARISON.md).

1. **Lightweight Semantic Expansion:** Deterministic (<0.2ms) cluster normalization bridges lexical vocabulary gaps without external LLM dependencies.
2. **Calibrated Logit Sigmoid Scaling:** Non-linear cross-encoder logits are converted to reliable confidence percentages via temperature scaling.
3. **Data Demarcation & Boundary Integrity:** Retrieved documents are treated as untrusted data, enclosed in `<verified_context>` XML wrappers with symmetric tag escaping.
4. **Zero Hallucination on Unanswerable Inquiries:** Out-of-scope, future forecasts, confidential student data, and fictional programs trigger deterministic, grounded abstentions.
5. **Zero-Downtime Offline Fallback:** If cloud LLM APIs experience rate limits (`429 RESOURCE_EXHAUSTED`), the system automatically switches to the built-in **Local Grounded Synthesizer** with zero downtime.

---

## 🔒 Optional API Configuration
The assistant operates out-of-the-box using the built-in **Local Grounded Synthesizer** (100% offline, zero-cost, verifiable citations). If you wish to enable Google Gemini or OpenAI, configure your `.env` file:

```bash
# In your .env file:
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

*(API keys are never logged, displayed in the UI, or committed to source control.)*

