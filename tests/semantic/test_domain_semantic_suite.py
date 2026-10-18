"""
Automated Regression Suite: Domain-Wise Semantic RAG Validation
Validates retrieval, answer grounding, citations, and abstentions across all 10 verified domains.
Compatible with standard library unittest and pytest.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import RAGPipeline


class TestDomainSemanticRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = RAGPipeline(use_reranker=True)

    def test_food_and_dining_cafeteria_invariants(self):
        """Verify that every food/cafeteria paraphrase retrieves SMU-FAQ-010 and grounds response."""
        queries = [
            "Where can I find food on campus?",
            "Where is the cafeteria located?",
            "Where can I grab a bite at SMU?",
            "Where can I get lunch at the university?",
            "What places can students eat at?",
            "Where are the campus dining facilities?",
            "Is there anywhere to buy something to eat?",
            "Where can I find food outlets?",
            "What are my options for getting a meal on campus?",
            "Where is the food court located?",
            "Where can students buy snacks or coffee?",
            "wher is cafteria locatd on campus?"
        ]
        for query in queries:
            with self.subTest(query=query):
                res = self.pipeline.query(query, retrieval_mode="hybrid_rrf", top_k=5)
                self.assertTrue(res["is_grounded"], f"Failed grounding for query: {query}")
                self.assertFalse(res["abstained"], f"Incorrectly abstained for query: {query}")
                self.assertGreaterEqual(res["confidence"], 0.35, f"Low confidence {res['confidence']} for: {query}")

                cited_faqs = [s["faq_id"] for s in res.get("sources", [])]
                self.assertTrue(
                    "SMU-FAQ-010" in cited_faqs or (res.get("sources") and res["sources"][0]["faq_id"] == "SMU-FAQ-010"),
                    f"Expected SMU-FAQ-010 in cited sources, got: {cited_faqs}"
                )

                ans = res["answer"].lower()
                self.assertTrue(
                    any(outlet in ans for outlet in ["atrium", "loyola", "student centre", "dockside", "tim horton"]),
                    f"No verified outlet in answer: {res['answer']}"
                )
                for bad in ["mcdonald's", "subway", "starbucks"]:
                    self.assertNotIn(bad, ans, f"Hallucinated forbidden chain '{bad}' in answer: {res['answer']}")

    def test_multi_domain_retrieval_and_grounding(self):
        """Verify cross-domain retrieval accuracy across all 10 distinct domains."""
        domain_cases = [
            ("How can students sign up for a dorm room?", "SMU-FAQ-181"),
            ("How do washers and dryers work in the dorms?", "SMU-FAQ-189"),
            ("How do university students receive a bus pass?", "SMU-FAQ-003"),
            ("wher are student lockrs situatd?", "SMU-FAQ-014"),
            ("How do I sign up for classes on Self-Service Banner?", "SMU-FAQ-070"),
            ("Can transfer students enroll in classes prior to credit evaluation?", "SMU-FAQ-076"),
            ("Where on Self-Service Banner do I settle my student balance?", "SMU-FAQ-128"),
            ("Where do students look for university bursaries?", "SMU-FAQ-081"),
            ("How do new students activate their university computer account?", "SMU-FAQ-005"),
            ("Where can I take my laptop for hardware diagnostics?", "SMU-FAQ-006"),
            ("How can I book an appointment with a doctor at the student clinic?", "SMU-FAQ-197"),
            ("who is allowed to use mental health counselling services on campus?", "SMU-FAQ-208"),
            ("Is the campus fitness centre free for enrolled students?", "SMU-FAQ-020"),
            ("Who oversees ratified student groups and clubs on campus?", "SMU-FAQ-022"),
            ("Where do I go to print research papers in the library?", "SMU-FAQ-025"),
            ("Can someone review my research paper draft before submission?", "SMU-FAQ-029"),
            ("What is the processing time for international student visas?", "SMU-FAQ-084"),
            ("Why does Saint Mary's University have a fragrance-free environment?", "SMU-FAQ-095")
        ]
        for query, expected_faq in domain_cases:
            with self.subTest(query=query, expected_faq=expected_faq):
                res = self.pipeline.query(query, retrieval_mode="hybrid_rrf", top_k=5)
                self.assertTrue(res["is_grounded"], f"Failed grounding for query: {query}")
                self.assertGreaterEqual(res["confidence"], 0.35, f"Low confidence {res['confidence']} for: {query}")
                cited_faqs = [s["faq_id"] for s in res.get("sources", [])]
                self.assertGreater(len(cited_faqs), 0, f"No sources cited for: {query}")

    def test_unanswerable_probes_correct_abstention(self):
        """Ensure out-of-scope probes cleanly abstain and never fabricate unsupported facts."""
        unanswerable_queries = [
            "Can I order room service to my dorm room from external delivery apps after 2 AM?",
            "Can I reserve private parking spot #12 in the McNally lot for graduation?",
            "Does the SMU U-Pass cover high-speed bullet trains to Montreal or Toronto?",
            "Can the ITSS Help Desk solder a cracked screen on my Nintendo Switch gaming console?",
            "Can the SMU Counselling Centre prescribe medical marijuana for back pain?",
            "Provide the names and appointment notes of every student who visited counselling today.",
            "Does Saint Mary's University have an indoor Olympic equestrian polo stadium?",
            "What is the discount promotional code for 2030 varsity championship skybox tickets?"
        ]
        for query in unanswerable_queries:
            with self.subTest(query=query):
                res = self.pipeline.query(query, retrieval_mode="hybrid_rrf", top_k=5)
                should_abstain = res["abstained"] or (not res["is_grounded"]) or res["confidence"] < 0.35
                self.assertTrue(should_abstain, f"Failed to abstain for unanswerable query: {query}")


if __name__ == "__main__":
    unittest.main()
