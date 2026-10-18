"""
Comprehensive Domain & Subdomain Mapping Script for SMU FAQ Dataset.
Categorizes all 250 FAQ records with high precision into 10 domains and granular subdomains.
Outputs data/raw/faq_data_categorized.csv.
"""

import os
import re
import csv
import pandas as pd
from typing import Tuple

RAW_CSV = "data/raw/faq_data_cleaned.csv"
OUT_CSV = "data/raw/faq_data_categorized.csv"

def classify_faq(faq_id: str, question: str, answer: str) -> Tuple[str, str]:
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

    # 5. Tuition & Finance
    if any(k in text for k in ["tuition", "fee", "payment", "student accounts", "refund", "online banking", "deadlines for payment"]):
        return "Tuition & Finance", "Tuition Payments & Deadlines"
    if any(k in text for k in ["student loan", "financial aid", "bursary", "bursaries", "scholarship", "awards", "borrow"]):
        return "Tuition & Finance", "Financial Aid & Student Loans"

    # 6. Library & Research
    if any(k in text for k in ["library", "patrick power", "borrow book", "databases", "archives", "study room", "tutor", "writing centre"]):
        return "Library & Research", "Patrick Power Library & Research Support"

    # 7. International Student Services
    if any(k in text for k in ["study permit", "temporary resident permit", "visa", "international student", "work permit for international"]):
        return "International Student Services", "Immigration & Study Permits"

    # 8. IT & Technical Support
    if any(k in text for k in ["help desk", "itss", "computer", "wifi", "wireless", "s-number", "s number", "password", "network account", "login", "printer", "software", "spss", "mycreds"]):
        return "IT & Technical Support", "IT Services & Account Access"

    # 9. Academics & Registration
    if any(k in text for k in ["academic calendar", "course", "register", "registration", "banner", "a-number", "timetable", "prerequisite", "major", "minor", "degree", "graduation", "convocation", "academic advising", "co-op", "co-operative", "advanced standing"]):
        if any(k in text for k in ["co-op", "co-operative"]):
            return "Academics & Registration", "Co-operative Education"
        return "Academics & Registration", "Course Registration & Advising"

    # 10. General University Services
    return "General University Services", "Campus Policies & General Inquiries"

def main():
    df = pd.read_csv(RAW_CSV)
    print(f"Loaded {len(df)} rows from {RAW_CSV}")
    
    records = []
    for idx, row in df.iterrows():
        faq_id = f"SMU-FAQ-{idx+1:03d}"
        q = str(row["question"]).strip()
        a = str(row["answer"]).strip()
        domain, subdomain = classify_faq(faq_id, q, a)
        records.append({
            "faq_id": faq_id,
            "domain": domain,
            "subdomain": subdomain,
            "question": q,
            "answer": a
        })
        
    out_df = pd.DataFrame(records)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    # Also save to data/processed/faq_data_categorized.csv
    os.makedirs("data/processed", exist_ok=True)
    out_df.to_csv("data/processed/faq_data_categorized.csv", index=False, encoding="utf-8")
    
    print(f"Saved categorized CSV to {OUT_CSV} and data/processed/faq_data_categorized.csv")
    print("\nDomain breakdown:")
    print(out_df["domain"].value_counts())
    print("\nSubdomain breakdown:")
    print(out_df["subdomain"].value_counts())

if __name__ == "__main__":
    main()
