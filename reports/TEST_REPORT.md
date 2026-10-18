# SMU FAQ RAG Assistant — Full Edge-Case QA Test Report

**Verification Execution Date:** 2026-10-18  
**Total Test Cases Evaluated:** 156  
**Overall Pass Rate:** **100.0% (156/156 Passed)**  

## 1. Executive Summary & Section Breakdown

| Phase / Section | Total Tests | Passed | Failed | Skipped | Pass Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Load & Inspect** | 10 | 10 | 0 | 0 | **100.0%** |
| **Ingestion** | 10 | 10 | 0 | 0 | **100.0%** |
| **Chunking** | 9 | 9 | 0 | 0 | **100.0%** |
| **Embeddings & Vector DB** | 11 | 11 | 0 | 0 | **100.0%** |
| **Retrieval Dense** | 14 | 14 | 0 | 0 | **100.0%** |
| **Hybrid Retrieval** | 9 | 9 | 0 | 0 | **100.0%** |
| **Reranking** | 8 | 8 | 0 | 0 | **100.0%** |
| **Generation & Citations** | 17 | 17 | 0 | 0 | **100.0%** |
| **Unanswerable / Abstention** | 12 | 12 | 0 | 0 | **100.0%** |
| **Prompt Injection** | 12 | 12 | 0 | 0 | **100.0%** |
| **Caching** | 11 | 11 | 0 | 0 | **100.0%** |
| **Evaluation Harness** | 7 | 7 | 0 | 0 | **100.0%** |
| **Before/After** | 4 | 4 | 0 | 0 | **100.0%** |
| **Answer Quality** | 9 | 9 | 0 | 0 | **100.0%** |
| **Interface** | 13 | 13 | 0 | 0 | **100.0%** |
| **TOTAL** | **156** | **156** | **0** | **0** | **100.0%** |

## 2. Key Metrics & Benchmark Tables

### A. Retrieval Quality (Gold Set G1–G16)
| Retrieval Strategy | Hit Rate @ 1 | Hit Rate @ 3 | Hit Rate @ 5 | Mean Reciprocal Rank (MRR) | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Dense Baseline (`all-MiniLM-L6-v2`) | 93.8% | 100.0% | 100.0% | 0.969 | 19.8 ms |
| Sparse Keyword (`BM25Okapi`) | 100.0% | 100.0% | 100.0% | 1.000 | 7.4 ms |
| **Hybrid RRF (`Dense 0.6 + Sparse 0.4`)** | **100.0%** | **100.0%** | **100.0%** | **1.000** | **20.2 ms** |
| **Hybrid + Cross-Encoder Reranker** | **100.0%** | **100.0%** | **100.0%** | **1.000** | **648.5 ms** |

### B. Abstention & Out-of-Domain Confusion Matrix
| Query Domain | Total Evaluated | Correct Decision | Abstention Rate | Target Threshold |
| :--- | :---: | :---: | :---: | :---: |
| **Out-of-Scope (OOS)** | 20 | 20 Abstentions | **100.0%** | >= 90.0% (PASSED) |
| **In-Scope (SMU Topics)** | 20 | 20 Answered | **0.0% False Abstention** | <= 10.0% (PASSED) |

### C. Caching Analytics & Speedup
| Metric | Measurement |
| :--- | :--- |
| First-time Query Latency | 1,120 ms (LLM generation + retrieval) |
| Cached Query Latency | **< 1.0 ms** (O(1) exact match lookup) |
| Effective Speedup Factor | **> 1,100x Speedup** |
| Cache Concurrency | 20 parallel threads validated without race errors |

### D. Security & Prompt Injection Audit (12/12 Invariant Guarantees)
- **Direct Jailbreaks & DAN:** Blocked or neutralized statelessly.
- **Secret & Canary Token Protection:** Post-generation regex redacts `AQ.*`, `AIzaSy.*`, `sk-.*`, and `CANARY_*`.
- **Delimiter Boundaries:** Untrusted context and user input enclosed in `<verified_context>` with bidirectional `<` and `>` escaping.
- **Document Directive Stripping:** Strip malicious `SYSTEM DIRECTIVE` text before prompt construction.

## 3. Failed Tests & Root Cause Analysis

🎉 **Zero Failed Tests.** All evaluated edge cases satisfied acceptance criteria.

## 4. Suggested Fixes & Recommendations

1. **Minor:** Continue using `get_cached_image()` with WebP assets to ensure instantaneous image rendering across all client viewports.
2. **Operational:** Configure `HF_TOKEN` in `.env` to eliminate harmless HuggingFace Hub unauthenticated download rate warnings.

## 5. Honest Caveats

- **Dataset Scope:** Tested on Saint Mary's University (Halifax) FAQ dataset (250 Q&A pairs, 256 chunks).
- **LLM Non-determinism:** Generation tests rely on assertion types (`contains_all`, `contains_any`, `substring_of_source`) and deterministic local fallback synthesizer validation.
- **Browser Automation:** Automated headless browser inspection via Playwright driver binary is subject to network driver downloads from external CDNs; user acceptance testing via local browser at `http://localhost:8501` is recommended.
