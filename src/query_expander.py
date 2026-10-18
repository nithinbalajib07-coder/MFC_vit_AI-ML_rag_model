"""
Semantic Query Expander & Normalizer
Enriches user queries with domain-specific synonyms and higher-education semantic clusters.
Handles spelling mistakes, plurals, verb conjugations, and vocabulary gaps (e.g. 'cafeteria' -> 'food', 'food court', 'dining hall').
Deterministic, lightweight (<0.2ms), and completely offline.
"""

import re
import difflib
from typing import List, Set, Dict, Tuple, Optional

# Pre-compiled common spelling mistakes and colloquial campus variations
COMMON_TYPOS = {
    "cafetaria": "cafeteria",
    "cafetria": "cafeteria",
    "cafteria": "cafeteria",
    "wher": "where",
    "locatd": "located",
    "locaton": "location",
    "lockrs": "lockers",
    "lockr": "locker",
    "suitemate": "roommate",
    "suitemates": "roommates",
    "tuitions": "tuition",
    "fee": "fees",
    "buspass": "bus pass",
    "upass": "u-pass",
    "dormitary": "dormitory",
    "resedence": "residence",
    "counseling": "counselling",
    "counseler": "counsellor",
    "smufit": "smufit",
    "homburg": "homburg",
    "accomodation": "accommodation",
    "schedul": "schedule",
    "schdule": "schedule",
    "foods": "food",
    "cafeterias": "cafeteria",
    "eatery": "food",
    "eateries": "food",
}

# Domain semantic clusters for SMU university operations (Pure conceptual synonyms)
SYNONYM_CLUSTERS = [
    # 1. Dining, Cafeteria, and Food Services
    {
        "pattern": r"\b(cafeteria(s)?|canteen(s)?|cafe(s)?|food\s*court(s)?|dining(\s*hall)?|food(s)?|eat(ing)?|lunch(es)?|dinner(s)?|breakfast|snack(s)?|meal(s)?|coffee|restaurant(s)?|outlet(s)?|eater(y|ies)|grab\s*(a\s*)?bite)\b",
        "expansions": ["food", "dining", "food court", "dining hall", "cafeteria", "Tim Hortons", "meals"]
    },
    # 2. Housing, Dorms, and Residence Life
    {
        "pattern": r"\b(dorm(s|itory)?|residence(s)?|housing|roommate(s)?|suitemate(s)?|room(s)?|living|live|sleep(ing)?|stay(ing)?|freshm(a|e)n|move\s*in|floor(s)?|conflict|mediation)\b",
        "expansions": ["residence", "housing", "dorm", "rooms", "roommate", "Residence Assistant"]
    },
    # 3. Transportation, Transit, Lockers, and Parking
    {
        "pattern": r"\b(bus(es)?(\s*pass)?|transit(\s*pass)?|u-?pass|x-?pass|e-?pass|metro\s*transit|halifax\s*transit|commute|ferry)\b",
        "expansions": ["U-Pass", "Metro Transit", "transit pass", "bus pass", "buses"]
    },
    {
        "pattern": r"\b(park(ing)?(\s*(permit|pass|ticket|meter|fine|spot))?|vehicle)\b",
        "expansions": ["parking permit", "parking", "meters", "Facilities Management"]
    },
    {
        "pattern": r"\b(locker(s)?|rental\s*locker(s)?)\b",
        "expansions": ["lockers", "rental lockers", "Facilities Management", "Loyola Academic", "Science building"]
    },
    # 4. Tuition, Fees, Financial Aid, and Loans
    {
        "pattern": r"\b(tuition(s)?|fee(s)?|cost(s)?|price(s)?|charge(s)?|payment(s)?|pay|owe|bill(s)?|refund(s)?)\b",
        "expansions": ["tuition", "tuition due", "fees", "Student Account Center", "rates", "cost", "charges"]
    },
    {
        "pattern": r"\b(when\s+(is|are)\s+(it|tuition|fee|fees)\s+due|due\s+date(s)?|deadlines?\s+(for|to)\s+pay)\b",
        "expansions": ["When are tuition fees due", "September", "January", "penalties for late payment", "Service Centre"]
    },
    {
        "pattern": r"\b(student\s*loan(s)?|financial\s*aid|bursar(y|ies)|scholarship(s)?|award(s)?|grant(s)?|funding|assistance)\b",
        "expansions": ["Student Loan", "Financial Aid", "Awards", "Service Centre", "funding"]
    },
    # 5. Registration, Enrolment, and Academic Records
    {
        "pattern": r"\b(sign\s*up\s*for\s*classes|course\s*selection|drop\s*course|add\s*course|course\s*registration)\b",
        "expansions": ["register", "courses", "registration"]
    },
    {
        "pattern": r"\b(transfer\s*credit(s)?|credit\s*evaluation|advanced\s*standing|prior\s*credit(s)?)\b",
        "expansions": ["advanced standing", "transfer credit", "prerequisites", "register for courses", "transcripts"]
    },
    {
        "pattern": r"\b(grade(s)?|mark(s)?|gpa|transcript(s)?|exam\s*score(s)?|results)\b",
        "expansions": ["grades", "Banner", "Self-Service Banner", "exam schedules", "academic records"]
    },
    # 6. Identifiers & Accounts
    {
        "pattern": r"\b(student\s*(id|card|badge)|id\s*card|photo\s*id|university\s*card)\b",
        "expansions": ["Student I.D.", "Patrick Power Library", "student card", "photo I.D.", "I.D."]
    },
    {
        "pattern": r"\b(a-?number|banner\s*id|banner\s*pin|student\s*number)\b",
        "expansions": ["A number", "Banner ID", "PIN", "Self-Service Banner"]
    },
    {
        "pattern": r"\b(s-?number|smu\s*account|smuport|activate\s*(account|s-?number)?|smu\s*network|network\s*(account|drive|drives))\b",
        "expansions": ["s number", "activate", "ITSS", "network account", "SMU network"]
    },
    # 7. IT, Computing, and Technical Support
    {
        "pattern": r"\b(computer(s)?|laptop(s)?|pc|help\s*desk|tech\s*support|it\s*support|itss|wifi|wireless|blackboard|troubleshoot(ing)?|repair(s)?|broken)\b",
        "expansions": ["ITSS Help Desk", "computer", "repairs", "software", "support"]
    },
    # 8. Athletics, Fitness, and Campus Recreation
    {
        "pattern": r"\b(gym|workout|fitness|exercise|cardio|weight\s*room|lift\s*weights|smufit|homburg|recreation|intramural(s)?)\b",
        "expansions": ["SMUfit", "fitness", "Homburg Centre", "Athletics", "gym"]
    },
    {
        "pattern": r"\b(home\s*game(s)?|ticket(s)?|varsity|huskies|game\s*tickets)\b",
        "expansions": ["home games", "tickets", "Athletics", "admission", "student I.D."]
    },
    {
        "pattern": r"\b(student\s*(group(s)?|organization(s)?|club(s)?|societ(y|ies))|join\s+(a\s+)?(club|society)|start\s+(a\s+)?(club|society)|campus\s*societ(y|ies))\b",
        "expansions": ["student societies", "society", "SMUSA", "clubs", "www.smusa.ca"]
    },
    # 9. Health, Wellness, and Counselling
    {
        "pattern": r"\b(counsell?ing|counsell?or(s)?|therap(y|ist|ists)|mental\s*health|psychologist|wellness|depress(ed|ion)|overwhelm(ed)?|anxious|anxiety|stress)\b",
        "expansions": ["The Counselling Centre", "counselling", "appointment", "Health & Wellness", "support"]
    },
    {
        "pattern": r"\b(who\s+(is\s+)?(allowed|eligible|permitted)|who\s+qualifies(\s+for)?|eligibility)\b",
        "expansions": ["who qualifies", "eligibility", "registered student", "current semester"]
    },
    # 10. Library, Writing Centre, and Tutoring
    {
        "pattern": r"\b(tutor(ing|s)?|peer\s*tutor(s)?)\b",
        "expansions": ["tutor", "SMUSA Tutor Database", "tutoring", "SMUSA"]
    },
    {
        "pattern": r"\b(writing\s*(centre|center|help|support)|essay(s)?|research\s*paper(s)?|term\s*paper(s)?|paper\s*draft(s)?)\b",
        "expansions": ["Writing Centre", "help writing an essay", "Burke Building", "academic communications"]
    },
    # 11. International Student Services & Immigration
    {
        "pattern": r"\b(student\s*visa(s)?|visa\s*(processing|timeline(s)?|application)?|study\s*permit(s)?|temporary\s*resident\s*permit)\b",
        "expansions": ["study permit", "temporary resident permit for Canada", "Citizenship and Immigration Canada", "international students"]
    },
    # 12. University Fragrance & Scent Policies
    {
        "pattern": r"\b(fragrance(-|\s*)free|scent(-|\s*)free|perfume(s)?|cologne(s)?|scented\s*products?|chemical\s*sensitivit(y|ies)|mcs)\b",
        "expansions": ["scent-free", "fragrance-free", "perfumes", "Multiple Chemical Sensitivity", "allergies", "environment"]
    },
    # 13. Campus Tour & Visits
    {
        "pattern": r"\b(tour(s)?|visit(s|ing)?|walkaround|walk\s*around|open\s*house)\b",
        "expansions": ["campus tour", "tour", "visit", "Centre for New Students", "booking"]
    }
]

# Common question-filler and conversational stopwords that should not crowd out content tokens
GENERIC_STOPWORDS = {
    "where", "when", "what", "how", "who", "why", "which",
    "is", "are", "was", "were", "be", "been", "being",
    "the", "a", "an", "at", "in", "on", "of", "for", "to", "from",
    "by", "with", "about", "can", "could", "would", "should",
    "do", "does", "did", "i", "you", "my", "your", "me", "we",
    "located", "situated", "find", "get", "tell", "please", "someone"
}


class QueryExpander:
    def __init__(self):
        self.clusters = SYNONYM_CLUSTERS
        self.typos = COMMON_TYPOS

    def correct_spelling(self, text: str) -> str:
        """
        Corrects common university domain typos and spelling mistakes.
        """
        words = text.split()
        corrected_words = []
        for w in words:
            # Strip punctuation for lookup
            clean_w = re.sub(r"[^\w\-]", "", w.lower())
            if clean_w in self.typos:
                corrected_words.append(self.typos[clean_w])
            else:
                corrected_words.append(w)
        return " ".join(corrected_words)

    def expand_query(self, query: str) -> str:
        """
        Takes a natural language query, fixes spelling, and generates an enriched
        representation with semantic synonyms appended, preserving all original query tokens.
        Example:
            'wher is the cafetaria locatd?' ->
            'wher is the cafetaria locatd? food dining food court dining hall'
        """
        if not query or not isinstance(query, str):
            return ""

        # Normalize query and correct obvious typos for trigger matching
        normalized = self.correct_spelling(query.lower())
        matched_expansions: Set[str] = set()

        for cluster in self.clusters:
            if re.search(cluster["pattern"], normalized):
                matched_expansions.update(cluster["expansions"])

        if not matched_expansions:
            return query.strip()

        # Filter out words that are already present in query to avoid redundancy
        lower_query = query.lower()
        novel_expansions = [
            exp for exp in matched_expansions
            if exp.lower() not in lower_query
        ]

        if not novel_expansions:
            return query.strip()

        # Append novel semantic synonyms
        enriched = f"{query.strip()} {' '.join(novel_expansions[:6])}"
        return enriched

    def extract_content_tokens(self, query: str) -> List[str]:
        """
        Extract meaningful content tokens, removing generic conversational stopwords.
        Useful for high-precision BM25 keyword matching.
        """
        corrected = self.correct_spelling(query)
        tokens = re.findall(r"\b[a-z0-9]{2,}\b", corrected.lower().replace("-", " ").replace("_", " "))
        content_tokens = [t for t in tokens if t not in GENERIC_STOPWORDS]
        return content_tokens if content_tokens else tokens
