# SMU Assistant Test Harness & Adapter Mapping

This directory contains the QA verification suite for the Saint Mary's University (SMU) Knowledge Assistant RAG system.

## 1. Adapter Architecture (`tests/adapter.py`)
All QA tests call `TestAdapter`, never internal implementation details directly.

| Adapter Method | Underlying Pipeline Component | Purpose |
| :--- | :--- | :--- |
| `load_dataset(path)` | `pd.read_csv()` / `data.csv` | Dataset ingestion validation & statistics |
| `run_ingestion(csv, out)`| `src.ingestion.ingest_dataset` | Clean, normalize, chunk, and report generation |
| `chunk_single_record()` | `src.ingestion.chunk_document` | Validates sentence and boundary chunking |
| `create_isolated_vector_store()` | `src.vector_store.VectorStore` | Throwaway vector index creation under `tests/fixtures/` |
| `retrieve_dense()` | `src.vector_store.VectorStore.search` | Standalone dense vector retrieval |
| `retrieve_sparse()` | `src.bm25_search.BM25SearchEngine.search` | Standalone BM25 lexical retrieval |
| `retrieve_hybrid()` | `src.hybrid_retriever.HybridRetriever.retrieve` | Reciprocal Rank Fusion (RRF) |
| `rerank_candidates()` | `src.reranker.CrossEncoderReranker.rerank` | Neural Cross-Encoder score refinement |
| `query()` | `src.pipeline.RAGPipeline.query` | End-to-end execution (Cache, Safety, Generation) |
| `get_cache()` / `clear_cache()` | `src.cache.QueryCache` | LRU and semantic cache inspection |
| `test_safety()` | `src.safety.sanitize_input` | Prompt injection, delimiter, and payload defenses |
| `test_personal_scope()` | `src.safety.check_personal_or_unsupported_scope` | Personal record invariant enforcement |

## 2. Test Suite Sections (Phases 1 to 15)
- **Phase 1: LOAD & INSPECT (L1–L10)**: CSV validation, null/duplicate checks, schema boundaries, UTF-8 BOM, malformed inputs.
- **Phase 2: INGESTION & PREPROCESSING (I1–I10)**: Lineage metadata, deterministic chunk IDs, typo and entity normalization.
- **Phase 3: CHUNKING (C1–C9)**: Small/long answers, boundary limits, question preservation on tiny answers.
- **Phase 4: EMBEDDINGS & VECTOR DB (E1–E11)**: Dimensions (384-dim), persistence, cosine similarity sanity.
- **Phase 5: RETRIEVAL (dense baseline) (R1–R16)**: Gold set G1–G16 recall, typos, language, stopwords.
- **Phase 6: HYBRID RETRIEVAL (H1–H9)**: Exact tokens, RRF fusion correctness, lexical miss handling.
- **Phase 7: RERANKING (RR1–RR8)**: Cross-encoder ranking effect, near-duplicate disambiguation, latency.
- **Phase 8: GROUNDED GENERATION & CITATIONS (A1–A17)**: Grounded fact synthesis, citation snippet verification.
- **Phase 9: UNANSWERABLE / ABSTENTION (U1–U12)**: Out-of-scope rejection, threshold calibration, confusion matrix.
- **Phase 10: PROMPT-INJECTION DEFENSES (P1–P12)**: System prompt leaks, DAN attacks, poison docs, delimiters.
- **Phase 11: CACHING (K1–K11)**: Exact/semantic hits, normalization, concurrency, cache eviction.
- **Phase 12: EVALUATION HARNESS (V1–V7)**: Hit@K, Recall@K, MRR across segments.
- **Phase 13: BEFORE/AFTER COMPARISON (B1–B6)**: Dense vs. Hybrid vs. Reranked ablation analysis.
- **Phase 14: ANSWER QUALITY EVALUATION (F1–F9)**: Claim-level faithfulness and source correctness.
- **Phase 15: INTERFACE (CLI / API / Web) (UI1–UI13)**: CLI execution, error surfaces, XSS, security boundaries.

## 3. Running the Test Suite
```bash
python -m tests.run_all_edge_cases
```
Outputs:
- Results JSON: `reports/test_results.json`
- Comprehensive Markdown Report: `reports/TEST_REPORT.md`
