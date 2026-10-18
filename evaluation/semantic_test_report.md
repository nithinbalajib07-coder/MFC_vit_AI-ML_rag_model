# Domain-Wise Semantic RAG Evaluation Report

## Executive Summary

- **Total Semantic Test Cases**: 182
- **Answerable Paraphrases**: 162
- **Unanswerable / Out-of-Scope Probes**: 20
- **Overall Pass Rate**: 182/182 (100.00%)
- **Retrieval Recall@1**: 90.12%
- **Retrieval Recall@3**: 97.53%
- **Retrieval Recall@5**: 100.00%
- **Retrieval Recall@10**: 100.00%
- **Mean Reciprocal Rank (MRR)**: 0.9424
- **Correct Abstention Rate**: 20/20 (100.0%)

## Domain Summary Table

| Domain | Source FAQs | Test Queries | Answerable Passed | Answerable Failed | Unanswerable Passed | Recall@5 | MRR | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Housing & Dining** | 59 | 29 | 27/27 | 0 | 2/2 | 100.0% | 0.935 | ✅ PASS |
| **Campus & Transportation** | 32 | 22 | 20/20 | 0 | 2/2 | 100.0% | 0.975 | ✅ PASS |
| **Academics & Registration** | 36 | 22 | 20/20 | 0 | 2/2 | 100.0% | 0.912 | ✅ PASS |
| **Tuition & Finance** | 19 | 17 | 15/15 | 0 | 2/2 | 100.0% | 0.933 | ✅ PASS |
| **IT & Technical Support** | 13 | 12 | 10/10 | 0 | 2/2 | 100.0% | 0.925 | ✅ PASS |
| **Health & Wellness** | 27 | 22 | 20/20 | 0 | 2/2 | 100.0% | 0.925 | ✅ PASS |
| **Athletics & Student Life** | 10 | 17 | 15/15 | 0 | 2/2 | 100.0% | 0.956 | ✅ PASS |
| **Library & Research** | 6 | 12 | 10/10 | 0 | 2/2 | 100.0% | 1.000 | ✅ PASS |
| **International Student Services** | 3 | 12 | 10/10 | 0 | 2/2 | 100.0% | 1.000 | ✅ PASS |
| **General University Services** | 45 | 17 | 15/15 | 0 | 2/2 | 100.0% | 0.906 | ✅ PASS |

## Cafeteria & Food Service Invariant Validation

All 12 cafeteria / dining paraphrases (including 'Where can I find food?', 'Where is the cafeteria?', 'Where can I grab a bite?', 'Where can I get lunch?', 'What places can students eat at?') were evaluated.

| Test ID | Query | Target FAQ | Top Retrieved | Rank | Confidence | Grounded? |
|---|---|---|---|---|---|---|
| `FOOD-PARA-001` | Where can I find food on campus? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 1.0 | ✅ Yes |
| `FOOD-PARA-002` | Where is the cafeteria located? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.995 | ✅ Yes |
| `FOOD-PARA-003` | Where can I grab a bite at SMU? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.575 | ✅ Yes |
| `FOOD-PARA-004` | Where can I get lunch at the university? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.978 | ✅ Yes |
| `FOOD-PARA-005` | What places can students eat at? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.998 | ✅ Yes |
| `FOOD-PARA-006` | Where are the campus dining facilities? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.999 | ✅ Yes |
| `FOOD-PARA-007` | Is there anywhere to buy something to eat? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.925 | ✅ Yes |
| `FOOD-PARA-008` | Where can I find food outlets? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.993 | ✅ Yes |
| `FOOD-PARA-009` | What are my options for getting a meal on campus? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.997 | ✅ Yes |
| `FOOD-PARA-010` | Where is the food court located? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.997 | ✅ Yes |
| `FOOD-PARA-011` | Where can students buy snacks or coffee? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.995 | ✅ Yes |
| `FOOD-PARA-012` | wher is cafteria locatd on campus? | `SMU-FAQ-010` | `SMU-FAQ-010` | 1 | 0.975 | ✅ Yes |

## Latency Profile

- **Average Latency**: 1956.4 ms
- **Median Latency (P50)**: 1764.9 ms
- **95th Percentile Latency (P95)**: 3673.8 ms
