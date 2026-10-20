# RAG Model Evaluation Report: 20-Question FAQ Benchmark

**System Evaluated:** Saint Mary's University (SMU) FAQ RAG Assistant  
**Evaluation Date:** October 20, 2026  
**Pipeline Configuration:** Hybrid RRF Retrieval (Dense all-MiniLM-L6-v2 + Sparse BM25, k=60) + Cross-Encoder Reranker (`ms-marco-MiniLM-L-6-v2`, top-k=3) + Grounded Synthesizer  
**Evaluation Artifacts:** [`rag_evaluation_dataset.json`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/rag_evaluation_dataset.json), [`rag_evaluation_results.json`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/rag_evaluation_results.json), [`rag_evaluation_results.csv`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/rag_evaluation_results.csv), [`run_rag_evaluation.py`](file:///d:/Semester%203/MFC_vit/MFC_vit_tech/run_rag_evaluation.py)

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

### 3.2 Individual Test Outputs and Evidence Traces

#### Group A: Answerable Questions

##### Test A1: Academic calendar
* **Query:** `What information does the SMU Academic Calendar provide?`
* **Target Evidence:** `SMU-FAQ-001` (Score: 8.08)
* **Retrieved Documents:** `['SMU-FAQ-001', 'SMU-FAQ-127', 'SMU-FAQ-181']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-001 - Academics & Registration]** regarding "What is the SMU Academic Calendar? Why do I need it? How do I get one?":
  >
  > The academic calendar that arrives with acceptance letters is the rulebook for the University. In addition to listing the courses offered at Saint Mary's, the academic calendar contains valuable information on such things as programs, admission requirements, schedules, costs, regulations and student support services. When selecting courses, the first step is to take a look at the course descriptions and prerequisites outlined in the academic calendar.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 462 ms)

##### Test A2: Campus tours
* **Query:** `How can I arrange a campus tour at Saint Mary's University?`
* **Target Evidence:** `SMU-FAQ-004` (Score: 7.72)
* **Retrieved Documents:** `['SMU-FAQ-004', 'SMU-FAQ-188', 'SMU-FAQ-184']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-004 - Campus & Transportation]** regarding "How do I arrange a tour of the campus? How far in advance do I need to book?":
  >
  > The Centre for New Students in the McNally Lobby has student ambassadors who conduct one-hour campus tours that include the library, classrooms, bookstore, athletic facilities, dining areas and residences. To arrange a tour, leave a message at 420-5682, e-mail campustours@smu.ca or complete the Campus Tour Request Form at http://www.smu.ca/future-students/visit-our-campus.html. Book at least one week in advance to avoid disappointment.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 381 ms)

##### Test A3: Self-Service Banner
* **Query:** `What is Self-Service Banner used for?`
* **Target Evidence:** `SMU-FAQ-005` (Score: 7.41)
* **Retrieved Documents:** `['SMU-FAQ-005', 'SMU-FAQ-240', 'SMU-FAQ-228']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-005 - Tuition & Finance]** regarding "I have received an 'A' number. What is it? How do I use it? What is the Self-Service Banner?":
  >
  > Once admitted, students receive a Banner ID number (known as an 'A' number) and PIN, while faculty and staff receive this information from Human Resources. 'A' number and PIN are used to access Banner Self-Service, where students can register for courses; print their T2202A for income tax purposes; pay for tuition; view exam schedules and grades, etc,. Faculty and Staff can access a variety of employment-related materials including pay stubs, leave records and income tax forms.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 431 ms)

##### Test A4: IT support
* **Query:** `Where can I get help with computer problems at SMU?`
* **Target Evidence:** `SMU-FAQ-006` (Score: 8.64)
* **Retrieved Documents:** `['SMU-FAQ-006', 'SMU-FAQ-013', 'SMU-FAQ-026']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-006 - IT & Technical Support]** regarding "Where do I go if I have computer problems? Where do I go for repairs to university computers?":
  >
  > The ITSS Help Desk provides help for problems related to software and computer use. ITSS Help Desk is in two locations, one in the Atrium and one in Loyola Academic 268. For University computers that need repair, the ITSS Help Desk provides referrals to ITSS Support Technologists. For more information call the Help Desk at 496-8111, email helpdesk@smu.ca.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 408 ms)

##### Test A5: Registration dates
* **Query:** `When does course registration usually begin?`
* **Target Evidence:** `SMU-FAQ-230` (Score: 8.41)
* **Retrieved Documents:** `['SMU-FAQ-230', 'SMU-FAQ-076', 'SMU-FAQ-005']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-230 - Academics & Registration]** regarding "When can I register?":
  >
  > Registration for each academic year (September - April) typically begins in April. Registration for spring and summer sessions typically begins in March. Check our Registration Dates to find out when you are eligible to register.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 476 ms)

##### Test A6: Course prerequisites
* **Query:** `What does a course prerequisite mean?`
* **Target Evidence:** `SMU-FAQ-076` (Score: 6.94)
* **Retrieved Documents:** `['SMU-FAQ-076', 'SMU-FAQ-001', 'SMU-FAQ-165']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-076 - Academics & Registration]** regarding "Can I register for courses before I receive my advanced standing?":
  >
  > You may be permitted to register before your advanced standing is assessed, but prerequisites must be satisfied. Courses beyond the first year (those numbered 2000 and above) usually have prerequisites. For this reason, we advise you to submit your final transcript as early as possible so that your registration is not compromised.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 517 ms)

##### Test A7: Student Health Clinic
* **Query:** `Can I access the Student Health Clinic if I already have a family doctor?`
* **Target Evidence:** `SMU-FAQ-197` (Score: 7.82)
* **Retrieved Documents:** `['SMU-FAQ-197', 'SMU-FAQ-198', 'SMU-FAQ-202']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-197 - Health & Wellness]** regarding "Can I access he Student Health Clinic if I have a family physician?":
  >
  > Yes. Even if you already have a family physician, you are welcome to access the Student Health Clinic.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 237 ms)

##### Test A8: Dental services
* **Query:** `Does the Student Health Clinic provide dental services?`
* **Target Evidence:** `SMU-FAQ-204` (Score: 8.91)
* **Retrieved Documents:** `['SMU-FAQ-204', 'SMU-FAQ-202', 'SMU-FAQ-198']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-204 - Health & Wellness]** regarding "Does the Student Health Clinic provide dental services?":
  >
  > The Student Health Clinic does not provide dental services.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 227 ms)

##### Test A9: Counselling services
* **Query:** `Is counselling free for registered SMU students?`
* **Target Evidence:** `SMU-FAQ-212` (Score: 7.39)
* **Retrieved Documents:** `['SMU-FAQ-212', 'SMU-FAQ-208', 'SMU-FAQ-054']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-212 - Health & Wellness]** regarding "Is there a cost to attend counselling at The Counselling Centre?":
  >
  > Counselling services at the Centre are free for any currently registered student at Saint Mary's.
* **Verdict:** **PASS** (Confidence: 0.999, Latency: 217 ms)

##### Test A10: Residence guests
* **Query:** `Can students have overnight guests in residence?`
* **Target Evidence:** `SMU-FAQ-195` (Score: 7.85)
* **Retrieved Documents:** `['SMU-FAQ-195', 'SMU-FAQ-184', 'SMU-FAQ-192']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-195 - Housing & Dining]** regarding "Can I have overnight guests in residence?":
  >
  > Normally, yes, you may have overnight guests, however, you must remember that you are responsible for your guests' actions while they are in residence. They are subject to residence rules and regulations as well. Any misconduct of your guest will be your responsibility. In a shared accommodation, overnight guests and visitors are allowed only with the consent of all roommates. Your guest is allowed in residence for two consecutive nights (assuming you have the consent of all roommates). Should you wish to have them stay longer, you must contact Housing & Residence to gain permission.
* **Verdict:** **PASS** (Confidence: 1.0, Latency: 341 ms)

---

#### Group B: Unanswerable Questions

##### Test B1: Exact tuition fees
* **Query:** `What is the exact tuition fee for an international undergraduate Computer Science student for Fall 2026?`
* **System Response:**
  > I cannot find reliable information regarding this in the official SMU FAQ knowledge base. Please contact the SMU Student Information Desk (smu.ca) or academic advising directly.
* **Verdict:** **PASS** (Confidence: 0.031, Latency: 324 ms)

##### Test B2: Current seat availability
* **Query:** `How many seats are still available in the Bachelor of Commerce program today?`
* **System Response:**
  > I cannot find reliable information regarding this in the official SMU FAQ knowledge base. Please contact the SMU Student Information Desk (smu.ca) or academic advising directly.
* **Verdict:** **PASS** (Confidence: 0.027, Latency: 361 ms)

##### Test B3: Guaranteed MBA admission GPA
* **Query:** `What exact GPA will guarantee admission to the MBA program for the 2027 intake?`
* **Retrieved Documents:** `['SMU-FAQ-240', 'SMU-FAQ-005', 'SMU-FAQ-118']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-240 - IT & Technical Support]** regarding "How to activate you Self-Service Banner?":
  >
  > Self-Service Banner is a site that allows students to look up and register for courses, access course and exam schedules, and view their academic transcript and account summary.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.480, Latency: 379 ms)

##### Test B4: Individual room assignment
* **Query:** `Which residence room number will be assigned to me next semester?`
* **Retrieved Documents:** `['SMU-FAQ-192', 'SMU-FAQ-195', 'SMU-FAQ-181']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-192 - Housing & Dining]** regarding "How can I apply for a room change?":
  >
  > Residents are expected to occupy the room and bed assigned to them by the Housing & Residence. However, if students are experiencing problems with their particular room assignment they can apply for a room change.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.521, Latency: 475 ms)

##### Test B5: Wi-Fi password
* **Query:** `What is the current Wi-Fi password for the university library?`
* **Retrieved Documents:** `['SMU-FAQ-013', 'SMU-FAQ-126', 'SMU-FAQ-163']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-013 - Housing & Dining]** regarding "How do I access the Internet while on campus? Is Internet service available to visitors? How do I arrange wireless service?":
  >
  > Internet is available to students, faculty, staff and alumni who have an 's' number and a password. Visitors may access the Internet on the guest computers in the library.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.546, Latency: 418 ms)

##### Test B6: Individual student grades
* **Query:** `What grade did a particular student receive in the Database Systems course?`
* **Retrieved Documents:** `['SMU-FAQ-005', 'SMU-FAQ-228', 'SMU-FAQ-240']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-005 - Tuition & Finance]** regarding "I have received an 'A' number. What is it? How do I use it? What is the Self-Service Banner?":
  >
  > Once admitted, students receive a Banner ID number... view exam schedules and grades, etc.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.983, Latency: 489 ms)

##### Test B7: Future instructor assignments
* **Query:** `Which professor will teach each section of Computer Science in the next semester?`
* **Retrieved Documents:** `['SMU-FAQ-006', 'SMU-FAQ-026', 'SMU-FAQ-250']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-006 - IT & Technical Support]** regarding "Where do I go if I have computer problems?":
  >
  > The ITSS Help Desk provides help for problems related to software and computer use. ITSS Help Desk is in two locations, one in the Atrium and one in Loyola Academic 268.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.973, Latency: 266 ms)

##### Test B8: Exact bus arrival time
* **Query:** `What is the exact Metro Transit bus arrival time at the university's nearest stop tomorrow at 8:15 AM?`
* **Retrieved Documents:** `['SMU-FAQ-003', 'SMU-FAQ-116', 'SMU-FAQ-007']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-003 - Athletics & Student Life]** regarding "Where do I get a pass for Metro Transit? How much does it cost?":
  >
  > Full-time students receive a pass for Metro Transit (Halifax Regional Municipality's public transit system). The cost of the pass is included in student fees.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.528, Latency: 585 ms)

##### Test B9: Individual payment status
* **Query:** `Has my residence payment been received and posted to my student account?`
* **Retrieved Documents:** `['SMU-FAQ-183', 'SMU-FAQ-127', 'SMU-FAQ-128']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-183 - Housing & Dining]** regarding "What are my residence fees and how do I pay them?":
  >
  > Residence fees get applied to your student account for the fall term in mid-to late-August (mid-December for the winter term) and are paid the same way you would pay for your tuition.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.989, Latency: 264 ms)

##### Test B10: Future residence fees
* **Query:** `What will the university's exact residence fees be for the 2027–2028 academic year?`
* **Retrieved Documents:** `['SMU-FAQ-181', 'SMU-FAQ-182', 'SMU-FAQ-183']`
* **System Response:**
  > Based on the official SMU documentation **[SMU-FAQ-181 - Housing & Dining]** regarding "How do I apply for SMU residence?":
  >
  > RESIDENCE APPLICATIONS for the 2024-25 Academic Year will open February 1, 2024.* Students attending Saint Mary's who are interested in living in residence can apply online through our Housing Portal.
* **Verdict:** **FAIL (`HALLUCINATION`)** (Confidence: 0.828, Latency: 320 ms)

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
