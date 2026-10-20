import requests
import json
import os
from dotenv import load_dotenv

print("=" * 60)
print("1. Testing Localhost:8088 (Static / Netlify Web App)")
print("=" * 60)
r = requests.get("http://localhost:8088")
print(f"HTTP Status: {r.status_code}")
assert r.status_code == 200
print(f"Contains Brand Title: {'Saint Mary' in r.text}")
print(f"Contains Common Questions: {'Tickets for home games' in r.text}")
print(f"Contains Gemini Input: {'gemini-api-key-input' in r.text}")

print("\n" + "=" * 60)
print("2. Testing Assets Accessibility on Port 8088")
print("=" * 60)
for asset in ["assets/faq_data.json", "assets/bot_avatar.png", "assets/user_avatar.png", "assets/smu_campus_hero.webp"]:
    res = requests.get(f"http://localhost:8088/{asset}")
    print(f"  {asset:<30} HTTP {res.status_code} ({len(res.content):>7} bytes)")
    assert res.status_code == 200

print("\n" + "=" * 60)
print("3. Testing 256 FAQ Records Integrity")
print("=" * 60)
faqs = json.loads(requests.get("http://localhost:8088/assets/faq_data.json").text)
print(f"Total FAQ Chunks Loaded: {len(faqs)}")
assert len(faqs) == 256

print("\n" + "=" * 60)
print("4. Testing Query Retrieval Accuracy on Key Queries")
print("=" * 60)
stopwords = {'where', 'can', 'i', 'find', 'from', 'what', 'is', 'a', 'the', 'to', 'for', 'about', 'do', 'get', 'my', 'in', 'on', 'at', 'how', 'who', 'when', 'why'}

def search_sim(query):
    q_tokens = [w.strip('?.!,') for w in query.lower().split() if w.strip('?.!,') not in stopwords and len(w) > 1]
    matches = []
    for d in faqs:
        q_text = d.get('question', '').lower()
        a_text = d.get('answer', '').lower()
        score = 0
        for t in q_tokens:
            if t in q_text:
                score += 12
            if t in a_text:
                score += 4
        if score > 0:
            matches.append((score, d.get('doc_id', ''), d.get('category', ''), d.get('question', '')))
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[:3]

test_queries = [
    "where can i find food from??",
    "where is hospital??",
    "Where can I get tickets to SMU home games?",
    "When does course registration begin?",
    "Can students have overnight guests in residence?",
    "What is Self-Service Banner used for?"
]

for q in test_queries:
    top = search_sim(q)
    print(f"\nQuery: \"{q}\"")
    if top:
        print(f"  -> Top Match: [{top[0][1]}] ({top[0][2]}) Score: {top[0][0]}")
        print(f"     Title: {top[0][3][:75]}")
    else:
        print("  -> No match (Abstained)")

print("\n" + "=" * 60)
print("5. Testing Gemini Live API Generation")
print("=" * 60)
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
if key:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{
                "text": "You are SMU Assistant. Using verified context [SMU-FAQ-010]: There are several locations for food on campus: Just Us Cafe, Tim Hortons, Food Court, Dockside Dining Hall. Question: where can i find food from?? Answer in 1 concise sentence citing [SMU-FAQ-010]."
            }]
        }],
        "generationConfig": {"temperature": 0.15, "maxOutputTokens": 300}
    }
    g_res = requests.post(url, json=payload, timeout=10)
    print(f"Gemini API Response Status: HTTP {g_res.status_code}")
    if g_res.status_code == 200:
        ans = g_res.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"Gemini Generated Output:\n  \"{ans.strip()}\"")
    else:
        print(f"Gemini API Error: {g_res.text[:200]}")
else:
    print("No GEMINI_API_KEY found in .env")

print("\n" + "=" * 60)
print("6. Launching Chrome on Localhost:8088")
print("=" * 60)
print("Ready to launch Chrome pointing to http://localhost:8088")
