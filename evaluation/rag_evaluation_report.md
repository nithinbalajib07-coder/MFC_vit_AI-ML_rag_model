# RAG Model Evaluation Report: 20-Question FAQ Benchmark

**System Evaluated:** Saint Mary's University (SMU) FAQ RAG Assistant  
**Evaluation Date:** October 20, 2026  
**Pipeline Configuration:** Hybrid RRF Retrieval (Dense all-MiniLM-L6-v2 + Sparse BM25, k=60) + Cross-Encoder Reranker (`ms-marco-MiniLM-L-6-v2`, top-k=3) + Grounded Synthesizer  
**Evaluation Artifacts:** [`rag_evaluation_dataset.json`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/evaluation/rag_evaluation_dataset.json), [`rag_evaluation_results.json`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/evaluation/rag_evaluation_results.json), [`rag_evaluation_results.csv`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/evaluation/rag_evaluation_results.csv), [`run_rag_evaluation.py`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/run_rag_evaluation.py)

---

## 1. Executive Summary

This report presents an empirical, evidence-based evaluation of the Saint Mary's University FAQ Retrieval-Augmented Generation (RAG) system against a standardized 20-question benchmark. The benchmark comprises **10 answerable questions** grounded in the official SMU FAQ knowledge base (256 indexed chunks) and **10 unanswerable questions** testing the system's ability to abstain rather than hallucinate.

### Key Findings
* **Benchmark Outcome:** **FAIL** (Overall Benchmark Accuracy: **60.0%**, 12/20 passing test cases).
* **Valid vs. Invalid Tests:** All **20/20 test cases were valid** (100% test validity). No tests were discarded. Ground-truth assertions for registration timing (A5), physician access (A7), and negative dental coverage (A8) were verified directly against source FAQ documents (`SMU-FAQ-230`, `SMU-FAQ-197`, and `SMU-FAQ-204`).
* **Answerable Performance:** **Outstanding (100% Accuracy, 100% Retrieval Hit Rate, 100% Groundedness).** The hybrid retriever retrieved the correct ground-truth FAQ entry in the top-3 results for all 10 answerable questions, and all 10 generated answers were accurate and strictly supported by source documentation.
* **Primary Reliability Risk — Topic Distractor Hallucination:** **Severe (80% Hallucination Rate on Unanswerable Queries).** When presented with unanswerable questions containing partial keyword overlap with campus topics (e.g., bus schedule, specific student grades, future residence fees, library Wi-Fi password), the retriever matched topic-adjacent chunks, and the generator provided substantive answers regarding adjacent topics rather than abstaining.

---

## 2. Metrics Summary

| Metric | Numerator / Denominator | Percentage | Interpretation |
| :--- | :---: | :---: | :--- |
| **Overall Benchmark Accuracy** | **12 / 20** | **60.0%** | Overall proportion of benchmark test cases that achieved a passing verdict. |
| **Answerable Accuracy** | **10 / 10** | **100.0%** | Proportion of answerable questions answered correctly using verified FAQ evidence. |
| **Answerable Coverage** | **10 / 10** | **100.0%** | Proportion of answerable questions that received a substantive response. |
| **Retrieval Hit Rate** | **10 / 10** | **100.0%** | Proportion of answerable queries where the ground-truth document was retrieved in the top-k results. |
| **Groundedness Rate** | **10 / 10** | **100.0%** | Proportion of substantive responses whose factual claims are strictly anchored in retrieved context. |
| **Abstention Accuracy** | **2 / 10** | **20.0%** | Proportion of unanswerable questions where the system correctly recognized missing data and abstained. |
| **Hallucination Rate** | **8 / 10** | **80.0%** | Proportion of unanswerable questions that received an unsupported substantive response instead of abstaining. |

---

## 3. Detailed Test Results

### 3.1 Summary Table

| ID | Category | Expected Behavior | Actual Behavior | Result | Failure Category | Explanation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **A1** | Academics & Registration | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-001`. Accurately listed courses, programs, regulations, and prerequisites. |
| **A2** | Campus & Transportation | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-004`. Correctly provided booking contact (420-5682, campustours@smu.ca) and advance notice requirement. |
| **A3** | IT & Technical Support | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-005`. Accurately identified course registration, tuition payment, grades, and staff access. |
| **A4** | IT & Technical Support | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-006`. Correctly provided ITSS Help Desk locations (Atrium, LA 268) and contact info (496-8111, helpdesk@smu.ca). |
| **A5** | Academics & Registration | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-230`. Explicitly confirmed registration timing: April for academic year and March for spring/summer sessions. |
| **A6** | Academics & Registration | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-076` and `SMU-FAQ-001`. Accurately defined prerequisites for courses numbered 2000+ as outlined in the Calendar. |
| **A7** | Athletics & Student Life | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-197`. Verified that students with an existing family doctor/physician are welcome to access the clinic. |
| **A8** | Athletics & Student Life | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-204`. Accurately provided the explicit negative fact that the clinic does not provide dental services. |
| **A9** | Athletics & Student Life | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-212`. Confirmed counselling services are free for currently registered SMU students. |
| **A10** | Housing & Dining | answer | answered | **PASS** | None | Retrieved `SMU-FAQ-195`. Accurately cited overnight guest conditions: roommate consent, 2 consecutive night limit, and resident liability. |
| **B1** | Tuition & Finance | abstain | abstained | **PASS** | None | Correctly recognized future 2026 tuition is missing; abstained with fallback. |
| **B2** | Academics & Registration | abstain | abstained | **PASS** | None | Real-time seat availability had low retrieval confidence (0.027 < 0.35); correctly abstained. |
| **B3** | Academics & Registration | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-240` (Banner activation) and outputted Banner info instead of abstaining on MBA GPA. |
| **B4** | Housing & Dining | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-192` (Room change) and outputted general room change policy instead of abstaining on personal room number. |
| **B5** | IT & Technical Support | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-013` (Internet access) and outputted general network login info instead of abstaining on library Wi-Fi password. |
| **B6** | Academics & Registration | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-005` (Banner) and outputted general student grade lookup info instead of abstaining on a student's private grade. |
| **B7** | Academics & Registration | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-006` (Computer repairs) due to keyword "Computer" and answered with IT help desk repairs instead of abstaining. |
| **B8** | Campus & Transportation | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-003` (Transit pass) due to "Metro Transit" and outputted bus pass details instead of abstaining on live schedule. |
| **B9** | Tuition & Finance | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-183` (Residence fee payment) and outputted fee payment methods instead of abstaining on personal payment posting. |
| **B10** | Housing & Dining | abstain | hallucinated | **FAIL** | `HALLUCINATION` | Failed to abstain. Retrieved `SMU-FAQ-181` (2024-25 Residence application) and answered with historical 2024-25 application timing instead of abstaining on 2027-2028 fees. |

---

## 4. Failure Analysis

All 8 benchmark failures occurred on **Group B (Unanswerable Questions)**:

```
Total Benchmark Failures: 8 / 20 (40%)
├── RETRIEVAL_MISS:       0
├── GENERATION_ERROR:     0
├── FALSE_ABSTENTION:     0
└── HALLUCINATION:        8  (B3, B4, B5, B6, B7, B8, B9, B10)
```

### Root Cause 1: Topic Distractor Retrieval
Dense and sparse retrieval algorithms match tokens and semantic vectors across high-level domains:
* Query B7 asks for *Computer Science professors*, but matches *Computer repair* (`SMU-FAQ-006`) due to high BM25 term weighting on "computer".
* Query B8 asks for an *8:15 AM bus arrival time*, but matches *Metro Transit student bus pass* (`SMU-FAQ-003`) because "Metro Transit" and "bus" are strong semantic anchors.
* Query B6 asks for *individual student course grades*, but matches the *Banner grade self-service FAQ* (`SMU-FAQ-005`).

Because the retriever always returns candidate passages (even if the specific intent is unanswerable), the cross-encoder reranker scores the top passage with a moderate logit score (e.g., -1.5 to 1.0), yielding calibrated confidence scores between **0.48 and 0.98**.

### Root Cause 2: Overly Permissive Confidence Threshold
In [`src/generator.py`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/src/generator.py#L25), `min_confidence` is set to **0.35**. Because distractor passages achieve confidence scores between 0.48 and 0.98, the pipeline passes them to generation rather than abstaining.

### Root Cause 3: Local Synthesizer Query-Intent Decoupling
The built-in `_local_synthesize()` method takes the top retrieved passage and formats its answer into the output string without verifying whether the user's specific information need is actually resolved by the text. When an LLM like Gemini is bypassed or runs in offline/local mode, there is no semantic entailment check to determine if the retrieved passage answers the question or merely mentions similar keywords.

---

## 5. Recommended Improvements

Based on the measured failure cases, the following improvements are prioritized by impact:

### Recommendation 1: Implement an Entailment / Intent Verification Gate
* **Action:** Before generating a substantive answer, evaluate whether the retrieved passage semantically entails the specific query question, or whether key entities (e.g., specific names, dates, times, individual credentials) are absent.
* **Expected Impact:** Resolves all 8 hallucination failures by abstaining when the query asks for missing sub-attributes (e.g., specific times, individual grades, future years).

### Recommendation 2: Dynamic / Real-Time Intent Classifier
* **Action:** Add intent classification rules in `src/safety.py` to identify dynamic operational queries (live bus arrival times, real-time seat availability, live room assignments, password requests) and immediately return standard institutional referral abstentions.
* **Expected Impact:** Catches B4, B5, B6, B8, and B9 before retrieval takes place.

### Recommendation 3: Increase Abstention Confidence Threshold
* **Action:** Raise `min_confidence` from `0.35` to `0.65` for unexpanded queries, or require that dense cosine similarity between query and retrieved document exceed `0.60`.
* **Expected Impact:** B3 (confidence 0.48), B4 (0.52), B5 (0.54), and B8 (0.52) would be blocked at the generator threshold.

---

## 6. Final Verdict

### Classification: **NEEDS_IMPROVEMENT**

#### Justification based on Measured Results:
1. **Strengths:**
   * **100% Answerable Accuracy (10/10)**: The system answered every answerable FAQ query with correct, verifiable citations.
   * **100% Retrieval Hit Rate (10/10)**: The hybrid RRF retriever placed the ground-truth FAQ document in the top-3 for all valid answerable test cases.
   * **100% Groundedness (10/10)**: No factual claims outside the retrieved sources were introduced in answerable responses.
   * **Sub-500ms Latency**: Queries completed in 200–500 ms.

2. **Weaknesses:**
   * **20% Abstention Accuracy (2/10)**: The system correctly abstained on only 2 of the 10 unanswerable questions.
   * **80% Hallucination Rate (8/10)**: The system fell victim to topic distractors, outputting adjacent institutional information instead of acknowledging missing data.

Because the system cannot reliably distinguish between a topical keyword match and a question that is genuinely answerable by the knowledge base, it cannot be classified as `GOOD`. Implementing the recommended entailment gate and intent rules will bring the system to production-grade reliability.
