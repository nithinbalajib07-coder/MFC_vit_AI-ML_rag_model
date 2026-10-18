"""
SMU FAQ Ingestion & Preprocessing Pipeline
Loads raw FAQ data, cleans text, infers category metadata, and creates chunked documents.
Generates a structured Ingestion Report detailing valid, invalid, duplicate, and skipped records.
"""

import os
import re
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_PATH = os.path.join("data", "raw", "faq_data_cleaned.csv")
PROCESSED_DATA_PATH = os.path.join("data", "processed", "processed_documents.json")
REPORT_PATH = os.path.join("data", "processed", "ingestion_report.json")
HF_DATASET_URL = "https://huggingface.co/datasets/tootooba/SMU_FAQDataset/raw/main/faq_data_cleaned.csv"


def download_raw_dataset(dest_path: str = RAW_DATA_PATH) -> str:
    """Download the raw FAQ dataset from Hugging Face if not already present."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        logger.info(f"Raw dataset already exists at {dest_path}")
        return dest_path

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    logger.info(f"Downloading dataset from {HF_DATASET_URL}...")
    import requests
    response = requests.get(HF_DATASET_URL, timeout=30)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Saved raw dataset to {dest_path} ({len(response.content)} bytes)")
    return dest_path


def clean_text(text: Any) -> str:
    """Clean whitespace, formatting anomalies, Unicode normalization, and punctuation."""
    if not isinstance(text, str):
        return ""
    # Normalize unicode spaces & dashes
    text = text.replace("\xa0", " ").replace("’", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    # Replace multiple whitespace/newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def validate_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates required fields in a record.
    Returns: (is_valid, error_reason)
    """
    if not isinstance(record, dict):
        return False, "Record is not a dictionary."
    
    q = record.get("question")
    a = record.get("answer")
    
    if q is None and a is None:
        return False, "Missing both question and answer fields."
    if q is None or pd.isna(q) or not str(q).strip() or str(q).strip().lower() == "nan":
        return False, "Question field is missing or empty."
    if a is None or pd.isna(a) or not str(a).strip() or str(a).strip().lower() == "nan":
        return False, "Answer field is missing or empty."
    
    clean_q = clean_text(str(q))
    clean_a = clean_text(str(a))
    if not clean_q or not clean_a:
        return False, "Record contains only whitespace after cleaning."
        
    return True, "Valid"


def classify_faq_domain_and_subdomain(question: str, answer: str) -> Tuple[str, str]:
    """Accurately classifies FAQ into 10 university domains and 17 granular subdomains."""
    q_lower = question.lower()
    a_lower = answer.lower()
    text = f"{q_lower} {a_lower}"

    # 1. Housing & Dining
    if any(k in text for k in ["food", "dining", "cafeteria", "tim hortons", "c-store", "dockside", "meal plan", "eat", "snack"]):
        if any(k in text for k in ["residence", "dorm", "housing", "roommate", "move-in", "move in"]):
            if any(k in text for k in ["food", "dining", "meal"]):
                return "Housing & Dining", "Campus Food & Residence Dining"
            return "Housing & Dining", "Residence Life & Housing"
        return "Housing & Dining", "Campus Dining & Food Outlets"
    
    if any(k in text for k in ["residence", "dorm", "housing", "roommate", "move-in", "move in", "loyola residence", "vanier", "rice"]):
        return "Housing & Dining", "Residence Life & Housing"

    # 2. Athletics & Student Life
    if any(k in text for k in ["game", "huskies", "varsity", "smufit", "homburg", "gym", "intramural", "athletics ticket", "athletics webpage"]):
        return "Athletics & Student Life", "Athletics & SMUfit Recreation"
    if any(k in text for k in ["smusa", "society", "societies", "student union", "student government"]):
        return "Athletics & Student Life", "Student Government & Societies"

    # 3. Health & Wellness
    if any(k in text for k in ["counselling", "counseling", "clinician", "therapist", "mental health", "crisis", "distress"]):
        return "Health & Wellness", "The Counselling Centre"
    if any(k in text for k in ["clinic", "doctor", "nurse", "blood drawn", "prescription", "medical", "health plan", "vaccine"]):
        return "Health & Wellness", "Student Health Clinic"

    # 4. International Student Services
    if any(k in text for k in ["study permit", "temporary resident permit", "study visa", "international student", "work permit for international"]):
        return "International Student Services", "Immigration & Study Permits"

    # 5. Campus & Transportation
    if any(k in text for k in ["transit", "bus", "metro transit", "u-pass", "upass", "xpass", "halifax transit"]):
        return "Campus & Transportation", "Public Transit & U-Pass"
    if any(k in text for k in ["parking", "park", "parking permit", "parking meters", "vehicle", "facilities management"]):
        return "Campus & Transportation", "Parking & Campus Permits"
    if any(k in text for k in ["locker", "lockers"]):
        return "Campus & Transportation", "Lockers & Campus Facilities"
    if any(k in text for k in ["tour", "campus tour", "directions", "map"]):
        return "Campus & Transportation", "Campus Tours & Navigation"

    # 6. Tuition & Finance
    if any(k in text for k in ["tuition", "fee", "payment", "student accounts", "refund", "online banking", "deadlines for payment"]):
        return "Tuition & Finance", "Tuition Payments & Deadlines"
    if any(k in text for k in ["student loan", "financial aid", "bursary", "bursaries", "scholarship", "awards"]):
        return "Tuition & Finance", "Financial Aid & Student Loans"

    # 7. Library & Research
    if any(k in text for k in ["library", "patrick power", "borrow book", "databases", "archives", "study room", "tutor", "writing centre"]):
        return "Library & Research", "Patrick Power Library & Research Support"

    # 8. IT & Technical Support
    if re.search(r"\b(itss|help\s*desk|computer|wifi|wireless|s-number|s\s*number|network\s*account|login|password|printer|software|spss|mycreds)\b", text):
        return "IT & Technical Support", "IT Services & Account Access"

    # 9. Academics & Registration
    if any(k in text for k in ["academic calendar", "course", "register", "registration", "banner", "a-number", "timetable", "prerequisite", "major", "minor", "degree", "graduation", "convocation", "academic advising", "co-op", "co-operative", "advanced standing"]):
        if any(k in text for k in ["co-op", "co-operative"]):
            return "Academics & Registration", "Co-operative Education"
        return "Academics & Registration", "Course Registration & Advising"

    # 10. General University Services
    return "General University Services", "Campus Policies & General Inquiries"


def infer_category(question: str, answer: str) -> str:
    """Infers high-level university domain."""
    domain, _ = classify_faq_domain_and_subdomain(question, answer)
    return domain


def infer_subdomain(question: str, answer: str) -> str:
    """Infers specific operational subdomain."""
    _, subdomain = classify_faq_domain_and_subdomain(question, answer)
    return subdomain


def build_documents(
    df: pd.DataFrame,
    max_chunk_words: int = 250
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Transforms FAQ rows into structured documents with metadata and chunking.
    Tracks validation metrics, duplicates, and skips.
    Returns: (documents, ingestion_report)
    """
    documents = []
    seen_qa = set()
    
    total_records = len(df)
    valid_count = 0
    invalid_records = []
    duplicates_count = 0
    
    for idx, row in df.iterrows():
        raw_rec = row.to_dict()
        is_valid, reason = validate_record(raw_rec)
        
        if not is_valid:
            invalid_records.append({"row_index": idx, "reason": reason, "raw": str(raw_rec)[:120]})
            continue
            
        question = clean_text(str(row["question"]))
        answer = clean_text(str(row["answer"]))
        qa_pair = (question.lower(), answer.lower())
        
        if qa_pair in seen_qa:
            duplicates_count += 1
            continue
        seen_qa.add(qa_pair)
        
        valid_count += 1
        category = str(row["domain"]).strip() if "domain" in row and pd.notna(row["domain"]) else infer_category(question, answer)
        subdomain = str(row["subdomain"]).strip() if "subdomain" in row and pd.notna(row["subdomain"]) else infer_subdomain(question, answer)
        faq_id = f"SMU-FAQ-{valid_count:03d}"
        
        words = answer.split()
        # If answer is reasonably sized, keep as single chunk
        if len(words) <= max_chunk_words:
            doc_text = f"Question: {question}\nAnswer: {answer}"
            documents.append({
                "doc_id": f"{faq_id}-C1",
                "chunk_id": f"{faq_id}-C1",
                "parent_id": faq_id,
                "faq_id": faq_id,
                "row_id": idx,
                "category": category,
                "domain": category,
                "subdomain": subdomain,
                "question": question,
                "original_question": question,
                "answer": answer,
                "text": doc_text,
                "chunk_index": 1,
                "total_chunks": 1,
                "chunk_count": 1,
                "word_count": len(doc_text.split()),
                "source": f"SMU FAQ Official Archive ({faq_id})"
            })
        else:
            # Chunk long answers by paragraph or sentence sliding window
            paragraphs = [p.strip() for p in answer.split("\n\n") if p.strip()]
            if len(paragraphs) <= 1:
                step = max_chunk_words - 50
                chunks = []
                for start_i in range(0, len(words), step):
                    chunks.append(" ".join(words[start_i:start_i + max_chunk_words]))
            else:
                chunks = paragraphs

            total_chunks = len(chunks)
            for c_idx, chunk_content in enumerate(chunks, 1):
                doc_text = f"Question: {question} (Part {c_idx}/{total_chunks})\nAnswer Section: {chunk_content}"
                documents.append({
                    "doc_id": f"{faq_id}-C{c_idx}",
                    "chunk_id": f"{faq_id}-C{c_idx}",
                    "parent_id": faq_id,
                    "faq_id": faq_id,
                    "row_id": idx,
                    "category": category,
                    "domain": category,
                    "subdomain": subdomain,
                    "question": question,
                    "original_question": question,
                    "answer": chunk_content,
                    "text": doc_text,
                    "chunk_index": c_idx,
                    "total_chunks": total_chunks,
                    "chunk_count": total_chunks,
                    "word_count": len(doc_text.split()),
                    "source": f"SMU FAQ Official Archive ({faq_id})"
                })

    report = {
        "records_loaded": total_records,
        "valid_records": valid_count,
        "invalid_records_count": len(invalid_records),
        "invalid_records_details": invalid_records,
        "duplicate_records_skipped": duplicates_count,
        "final_indexed_chunks": len(documents),
        "columns_detected": list(df.columns),
        "status": "SUCCESS"
    }

    logger.info(
        f"Ingestion completed: {total_records} rows loaded, {valid_count} valid, "
        f"{duplicates_count} duplicates skipped, {len(invalid_records)} invalid, "
        f"{len(documents)} final chunks created."
    )
    return documents, report


def run_ingestion(
    raw_path: str = RAW_DATA_PATH,
    output_path: str = PROCESSED_DATA_PATH,
    report_path: str = REPORT_PATH
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Runs end-to-end ingestion pipeline and saves processed documents & structured report."""
    download_raw_dataset(raw_path)
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded raw FAQ CSV with shape: {df.shape}")
    
    docs, report = build_documents(df)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
        
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved processed documents to {output_path}")
    logger.info(f"Saved ingestion report to {report_path}")
    return docs, report


def load_raw_data(csv_path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Loads and validates raw FAQ CSV file."""
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        raise ValueError(f"Target dataset file is missing or empty (0 bytes): {csv_path}")
    df = pd.read_csv(csv_path)
    if "question" not in df.columns or "answer" not in df.columns:
        missing = [c for c in ["question", "answer"] if c not in df.columns]
        raise ValueError(f"Dataset missing required column(s): {missing}")
    return df


def chunk_document(record: Dict[str, Any], max_chunk_words: int = 250, **kwargs) -> List[Dict[str, Any]]:
    """Chunks a single FAQ record into structured chunk dictionaries."""
    df = pd.DataFrame([record])
    docs, _ = build_documents(df, max_chunk_words=max_chunk_words)
    return docs


if __name__ == "__main__":
    run_ingestion()
