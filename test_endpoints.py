#!/usr/bin/env python
"""Manual endpoint testing script."""

import requests

BASE_URL = "http://localhost:5000"

# Test 1: AI text
ai_text = (
    "The battle between Satoru Gojo and Ryomen Sukuna stands as one of the most epic and breathtaking confrontations in the history of anime and manga. "
    "Gojo, with his unparalleled Infinity and the awe-inspiring Six Eyes, represents the pinnacle of jujutsu sorcery in the modern era. "
    "However, Sukuna, the King of Curses, is a formidable opponent whose raw power and tactical brilliance cannot be overstated. "
    "This clash of titans raises fascinating questions about the nature of strength, strategy, and what it truly means to be the strongest. "
    "Ultimately, both combatants push each other to their absolute limits, making this fight a testament to the incredible storytelling of Gege Akutami. "
    "The practice is to hold the structure firmly enough to carry you through resistance, but loosely enough to interrogate it when it stops serving growth."
    "So yes — it's showing up when you don't want to, but with enough self-awareness to know whether you're building something or just performing effort."
)

# Test 2: Human text
human_text = (
    "Kenny is a natural liar, narcissist, but a nice and likeable guy. "
    "He was pretty extroverted as a kid and didn't care what people thought of him. And he matured as he grew to dull out those negative personality traits.  And now as he has furthered matured to a point where he's actually self aware of his traits and how it may affect others, but still actively displays it.  "
    "His home environment most likely and other factors such as his narcissism to crave attention. This leads to Zhen, the first person he considered to 'care about him' in this certain period of his life. "
    "But this made him to clingy and he is now in a point of denial. He's previously said that he no longer cares about Zhen but is very clear he still does. And I feel in some sort of way he's being kind of manipulative here.  "
    "Not to mention that whilst Kenny was in bored, Zhen and Simon were actively dating, but despite that Kenny only cared about his personal feelings, and  would attempt to isolate himself with Zhen and eventually beginning to date her. And lead Zhen to break up with Simon. "
    "Furthermore Kenny once stated that he'd never replace Zhen. But a few weeks ago he stated he had a new 'bestie' but weren't dating. Which in my eyes seemed like a replacement. And if this point was brought up to him and he'd agreed that it was some sort of replacement he'd claim something along the lines of not letting Zhen affect him and how'd he moved on."
    "Which is a reasonable, but the point that I'm leading into is that he actively begged her to stay. And now takes some sort of high road acting like he was somehow the bigger man, which I personally dislike.  To further clarify on what I mean on taking the high road is how he states he couldn't take her bipolar disorder and all 'the things she's done'."
    "But despite this he clearly could take it as he begged for another chance, but now theres no chance of reignition of their relationship, now he couldn't deal with her. And in this situation where the prisoner-"
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
        print(f"LLM Signal Score: {result.get('llm_sig', 'N/A')}")
        print(f"Stylometric Signal Score: {result.get('stylo_signal', 'N/A')}")
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
