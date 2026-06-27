# M5 Implementation Summary

## Overview
Milestone 5 is complete. The production layer is fully wired: all submissions are recorded in a structured audit log, the `/appeal` endpoint enforces all three validation guards (400 / 404 / 409), and `/log` returns the complete chronological history. Rate limits are applied to all three endpoints. A new endpoint test suite covers the full request/response contract.

## Files Modified

### 1. `app.py`

**New module-level state** (added after limiter setup):
```python
audit_log = []       # chronological list of all classification and appeal entries
content_status = {}  # content_id → "classified" | "under_review"
```
Both are in-memory for this implementation. `audit_log` is the source of truth returned by `/log`; `content_status` is the fast lookup used by `/appeal` to validate content_id existence and detect duplicate appeals.

**`/submit` — now writes to audit log:**
After computing the label, appends a classification entry and registers the content_id before returning:
```python
audit_log.append({
    "content_id": content_id,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "type": "classification",
    "confidence_score": round(confidence_score, 4),
    "label_key": label["label_key"],
})
content_status[content_id] = "classified"
```

**`/appeal` — fully implemented (was a stub):**

Rate limit: `5 per minute`

Validation order and HTTP codes:
| Check | Condition | Response |
|-------|-----------|----------|
| Missing / blank `reasoning` | `not reasoning or not reasoning.strip()` | 400 |
| Missing `content_id` | `not content_id` | 400 |
| Unknown `content_id` | `content_id not in content_status` | 404 |
| Duplicate pending appeal | `content_status[content_id] == "under_review"` | 409 |

On success: updates `content_status[content_id] = "under_review"`, appends appeal entry to `audit_log`, returns 200 with `status: "under_review"`.

**`/log` — fully implemented (was a stub):**

Rate limit: `30 per minute`

Returns the full `audit_log` list as a JSON array. No filtering or pagination — chronological order, all entry types included.

**New import:** `from datetime import datetime, timezone` (for ISO 8601 UTC timestamps).

### 2. `tests/test_app.py` (new file)

13 tests across three classes using Flask's built-in test client. All signal functions are mocked to `return_value=0.5` in submit-path tests to eliminate Groq API dependency.

**Fixture setup:**
- `clear_state` (`autouse=True`): clears `audit_log`, `content_status`, and rate-limiter storage (`limiter._storage.reset()`) before and after every test.
- `client`: sets `RATELIMIT_ENABLED = False` and yields a `app.test_client()` instance.

**`TestSubmitEndpoint` (F1–F4):**
- F1: Valid text → 200, all five required keys present
- F2: Empty text string → 400
- F3: Missing JSON body → 400
- F4: Successful submit → `audit_log` contains one `classification` entry with correct fields

**`TestAppealEndpoint` (G1–G6):**
- G1: Missing `reasoning` → 400
- G2: Empty `reasoning` string → 400
- G3: Unknown `content_id` → 404
- G4: Valid appeal after submit → 200, `status == "under_review"`
- G5: Duplicate appeal on same `content_id` → 409
- G6: Successful appeal → `audit_log` contains an `appeal` entry with correct `content_id`, `status`, and `reasoning`

**`TestLogEndpoint` (H1–H3):**
- H1: Empty log → 200, response is a list
- H2: After one submit → list contains one `classification` entry
- H3: After submit + appeal → list contains two entries in order (`classification` first, `appeal` second)

## Test Results

```
44 passed in 2.24s
```

### Test Breakdown
- `TestSubmitEndpoint` (F1–F4): 4 new tests — all pass
- `TestAppealEndpoint` (G1–G6): 6 new tests — all pass
- `TestLogEndpoint` (H1–H3): 3 new tests — all pass
- `TestLLMSignal` (A1–A8): 8 tests — unchanged, all pass
- `TestCombineSignals` (B1–B5): 5 tests — unchanged, all pass
- `TestLabelSelector` (C1–C8): 8 tests — unchanged, all pass
- `TestIntegration` (D1–D3): 3 tests — require `GROQ_API_KEY`, pass when key is present
- `TestStylometricSignal` (E1–E7): 7 tests — unchanged, all pass

## Design Notes

1. **`content_status` as a separate dict:** Rather than scanning `audit_log` to find a content_id's current status, `content_status` provides O(1) lookup. This keeps both the 404 check (existence) and 409 check (duplicate) fast as the log grows.

2. **Appeals do not trigger re-classification:** An appeal updates status and appends a log entry. The original classification entry is never modified — the log is append-only. Human review happens out-of-band.

3. **Validation order in `/appeal`:** Reasoning is validated before content_id existence is checked. This is intentional: a missing reasoning field is a client error that should be caught before the server performs a lookup, and it gives clearer error messages.

4. **UTC ISO 8601 timestamps:** `datetime.now(timezone.utc).isoformat()` produces timezone-aware strings (e.g., `2026-06-25T20:01:33.876774+00:00`). This ensures log entries are unambiguous across environments.

5. **Rate-limiter reset in tests:** Flask-Limiter's in-memory storage persists across test cases within a run. Without `limiter._storage.reset()` in the `autouse` fixture, the 5/min appeal limit would trigger mid-suite (G5's second appeal would see the counts from G1–G4 and return 429 instead of 409). The reset clears all counters before each test.

## Running the Tests

```bash
# All unit tests (no API key needed)
python -m pytest tests/ -v -k "not integration"

# Full suite (requires GROQ_API_KEY in .env)
python -m pytest tests/ -v

# Manual smoke test
python app.py  # terminal 1

# terminal 2 — full flow:
# 1. Submit text
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "She woke up tired. Made coffee. Still exhausted."}' | python -m json.tool

# 2. Copy the content_id from the response, then appeal:
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "<paste-id>", "reasoning": "I wrote this myself."}' | python -m json.tool

# 3. Confirm duplicate appeal is blocked:
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "<paste-id>", "reasoning": "Trying again."}' | python -m json.tool
# Expected: 409 Conflict

# 4. View full audit log:
curl -s http://localhost:5000/log | python -m json.tool
```

## Files Changed Summary

| File | Status | Changes |
|------|--------|---------|
| `app.py` | Modified | Added `audit_log`, `content_status`; `/submit` writes to log; `/appeal` fully implemented with 400/404/409 guards and rate limit; `/log` returns audit log with rate limit; added `datetime` import |
| `tests/test_app.py` | Created | 13 endpoint tests (F1–F4, G1–G6, H1–H3); `autouse` fixture resets log, status, and rate-limiter storage |
| `docs/M5_IMPLEMENTATION_SUMMARY.md` | Created | This file |

## Next Steps (Gradio Frontend)

- Build a Gradio interface that connects to the three Flask endpoints
- Submit tab: text input → calls `POST /submit` → displays `label_text`, `label_detail`, confidence score, and `content_id`
- Appeal tab: `content_id` + reasoning inputs → calls `POST /appeal` → shows confirmation or error
- Log tab: button → calls `GET /log` → renders entries as a table or formatted JSON
- The Flask app must be running on `localhost:5000` before launching the Gradio frontend
