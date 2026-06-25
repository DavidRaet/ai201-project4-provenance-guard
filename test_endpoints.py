#!/usr/bin/env python
"""Manual endpoint testing script."""

import requests

BASE_URL = "http://localhost:5000"

# Test 1: AI text
ai_text = (
    "Discipline is the sustained execution of chosen behavior independent of mood, motivation, or circumstance."
    "When high performers say 'be disciplined,' they're not describing rigid self-punishment — they're pointing to a kind of internal governance that operates below the noise of feeling."
    "Philosophically, it sits at the intersection of autonomy (the capacity to act from principle) and identity (becoming the kind of person for whom certain actions are non-negotiable)."
    "So discipline is less about force and more about architecture — designing your environment and commitments so that the right action becomes the path of least resistance."
    "But there's a failure mode here: discipline without reflection calcifies into rigidity, where the structure itself becomes the goal rather than what it was built to serve."
    "The practice is to hold the structure firmly enough to carry you through resistance, but loosely enough to interrogate it when it stops serving growth."
    "So yes — it's showing up when you don't want to, but with enough self-awareness to know whether you're building something or just performing effort."
)

# Test 2: Human text
human_text = (
    "TaeKwonDo is the art of kicking and punching; dating back thousands of years ago."
    "That was what I had initially thought when I first began my training.  "
    "However, the more I immersed myself in the art of TaeKwonDo, the more I began to realize that there was more to TaeKwonDo than its history and combat sport. "
    "That begs the question, “What did I learn from TaeKwonDo?” Behind all the various techniques of kicking and punching of TaeKwonDo, it taught self-improvement.  "
    "With the five core tenets of TaeKwonDo always being recited at the end of every class: Courtesy, Integrity, Self-Control, Perseverance, and Indomitable Spirit, I began to understand that TaeKwonDo was teaching a significant lesson to be the best versions of yourselves. "
)

# Test 3: Ambiguous text
ambiguous_text = (
    "The city had changed. Marcus noticed it in the way the old coffee shop on 5th "
    "had been replaced by a co-working space, all exposed brick and ergonomic chairs. "
    "Studies suggest that urban gentrification often displaces long-term residents, "
    "though local business owners report mixed outcomes depending on their lease "
    "structures and foot traffic patterns."
)

tests = [
    ("AI-generated text", ai_text, "AI_HIGH"),
    ("Human-written text", human_text, "HUMAN_HIGH"),
    ("Ambiguous text", ambiguous_text, "UNCERTAIN"),
]

print("=" * 70)
print("Testing Provenance Guard /submit endpoint")
print("=" * 70)

for test_name, text, expected_label in tests:
    payload = {"text": text}
    try:
        response = requests.post(f"{BASE_URL}/submit", json=payload, timeout=10)
        result = response.json()

        print(f"\nTest: {test_name}")
        print(f"Status: {response.status_code}")
        print(f"Confidence Score: {result.get('confidence_score', 'N/A')}")
        print(f"Label Key: {result.get('label_key', 'N/A')}")
        print(f"Label Text: {result.get('label_text', 'N/A')}")
        print(f"Expected: {expected_label}")

        if result.get("label_key") == expected_label:
            print("✓ PASS")
        else:
            print("✗ FAIL - label mismatch")

    except requests.exceptions.ConnectionError:
        print(f"\n✗ ERROR: Could not connect to {BASE_URL}")
        print("  Make sure the Flask app is running: python app.py")
        break
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

print("\n" + "=" * 70)
print("Testing rate limit (10 per minute)")
print("=" * 70)

payload = {"text": "test"}
success_count = 0
fail_count = 0

for i in range(9):
    try:
        response = requests.post(f"{BASE_URL}/submit", json=payload, timeout=5)
        if response.status_code == 200:
            success_count += 1
            print(f"Request {i + 1}: 200 OK")
        elif response.status_code == 429:
            fail_count += 1
            print(f"Request {i + 1}: 429 Rate Limited ✓")
        else:
            print(f"Request {i + 1}: {response.status_code}")
    except Exception as e:
        print(f"Request {i + 1}: ERROR - {e}")
        break

print(f"\nSuccessful: {success_count}, Rate Limited: {fail_count}")
if fail_count > 0:
    print("✓ Rate limiting is working correctly")
else:
    print("✗ Rate limiting did not trigger as expected")
