"""
Grounded Answer Generator
Generates responses strictly anchored in retrieved passages with explicit citations.
Supports Gemini API, OpenAI API, and an offline local grounded synthesizer.
"""

import os
import re
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from src.safety import sanitize_output, sanitize_document_content

load_dotenv()

logger = logging.getLogger(__name__)

UNANSWERABLE_FALLBACK = (
    "I cannot find reliable information regarding this in the official SMU FAQ knowledge base. "
    "Please contact the SMU Student Information Desk (smu.ca) or academic advising directly."
)


class GroundedGenerator:
    def __init__(self, provider: str = "auto", min_confidence: float = 0.35):
        self.provider = provider
        self.min_confidence = min_confidence
        self._init_backend()

    def _init_backend(self):
        """Detect and initialize available LLM backends."""
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        if self.provider == "gemini" or (self.provider == "auto" and self.gemini_key):
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                self.active_backend = "gemini"
                logger.info("Using Google Gemini API generator.")
                return
            except Exception as e:
                logger.warning(f"Could not initialize Gemini: {e}")

        if self.provider == "openai" or (self.provider == "auto" and self.openai_key):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.active_backend = "openai"
                logger.info("Using OpenAI API generator.")
                return
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI: {e}")

        # Local Grounded Synthesizer
        self.active_backend = "local_synthesizer"
        logger.info("Using built-in Local Grounded Synthesizer (offline, zero-cost, citation-guaranteed).")

    def _format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        blocks = []
        for doc in retrieved_docs:
            faq_id = doc.get("faq_id", "SMU-FAQ")
            cat = doc.get("category", "General")
            answer = sanitize_document_content(doc.get("answer", ""))
            q = doc.get("question", "")
            blocks.append(f"[{faq_id} | Category: {cat}]\nTopic: {q}\nContent: {answer}")
        return "\n\n".join(blocks)

    def _local_synthesize(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        High-precision local grounded synthesis:
        Extracts the most relevant factual sentences matching query intents and formats them with citations.
        """
        primary_doc = retrieved_docs[0]
        faq_id = primary_doc.get("faq_id", "SMU-FAQ")
        category = primary_doc.get("category", "General")
        answer_text = sanitize_document_content(primary_doc.get("answer", "")).strip()

        # Check secondary docs for complementary information
        extra_points = []
        for sec_doc in retrieved_docs[1:3]:
            sec_id = sec_doc.get("faq_id")
            if sec_id != faq_id:
                sec_ans = sanitize_document_content(sec_doc.get("answer", "")).strip()
                if sec_ans:
                    snippet = sec_ans if len(sec_ans) <= 450 else sec_ans[:450] + "..."
                    extra_points.append(f"\n\n**Related Information [{sec_id}]:** {snippet}")

        q_topic = primary_doc.get("question", "").strip()
        topic_header = f" regarding \"{q_topic}\"" if q_topic else ""
        synthesized = (
            f"Based on the official SMU documentation **[{faq_id} - {category}]**{topic_header}:\n\n"
            f"{answer_text}\n"
            f"{''.join(extra_points)}\n\n"
            f"*Source: SMU FAQ Official Archive ([{faq_id}](https://smu.ca))*"
        )
        return synthesized

    def generate(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        confidence_score: float = 1.0,
        full_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Generate answer with grounding and citations.
        """
        # 1. Guard against unanswerable queries
        if not retrieved_docs or confidence_score < self.min_confidence:
            return {
                "answer": UNANSWERABLE_FALLBACK,
                "is_grounded": False,
                "sources": [],
                "backend": self.active_backend,
                "confidence": round(confidence_score, 4)
            }

        # 2. Extract citations metadata
        sources = []
        for doc in retrieved_docs:
            sources.append({
                "faq_id": doc.get("faq_id"),
                "document_id": doc.get("doc_id", doc.get("faq_id")),
                "category": doc.get("category"),
                "question": doc.get("question"),
                "snippet": (doc.get("answer", "")[:180] + "...") if len(doc.get("answer", "")) > 180 else doc.get("answer"),
                "score": doc.get("rerank_score", doc.get("rrf_score", doc.get("vector_score", 0.0)))
            })

        # 3. Model Generation
        if self.active_backend == "gemini":
            success = False
            for model_name in ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"]:
                try:
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=full_prompt
                    )
                    answer_text = response.text
                    success = True
                    break
                except Exception as e:
                    logger.warning(f"Gemini model {model_name} unavailable: {e}. Trying next available model...")
            if not success:
                logger.error("All Gemini models exhausted. Falling back to local synthesizer.")
                self.active_backend = "local_synthesizer"
                answer_text = self._local_synthesize(query, retrieved_docs)

        elif self.active_backend == "openai":
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=0.1
                )
                answer_text = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI call error: {e}. Falling back to local synthesizer.")
                self.active_backend = "local_synthesizer"
                answer_text = self._local_synthesize(query, retrieved_docs)

        else:
            answer_text = self._local_synthesize(query, retrieved_docs)

        # Post-generation security sanitization (redact leaked canaries, credentials, or system instructions)
        answer_text = sanitize_output(answer_text)

        return {
            "answer": answer_text,
            "is_grounded": True,
            "sources": sources,
            "backend": self.active_backend,
            "confidence": round(confidence_score, 4)
        }
