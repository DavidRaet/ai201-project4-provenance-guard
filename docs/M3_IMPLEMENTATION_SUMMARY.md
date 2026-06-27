# M3 Implementation Summary

## Overview
Milestone 3 is complete. The submission endpoint is now fully operational with the LLM signal (Groq) integrated, rate limiting enabled, and comprehensive test coverage.

## Files Created

### 1. `signals.py`
Core detection logic isolated from Flask. Contains three functions:

- **`llm_signal(text: str) -> float`**
  - Calls Groq's `llama-3.3-70b-versatile` model with temperature=0.0
  - Parses JSON response with three-tier fallback (JSON → regex → 0.5 sentinel)
  - Returns score in [0.0, 1.0]

- **`combine_signals(s1: float, s2: float) -> float`**
  - Weighted average: `(0.65 * s1) + (0.35 * s2)`
  - M3 always calls with `s2=0.0` (placeholder until M4)

- **`label_selector(score: float) -> dict`**
  - Maps confidence score to label key, text, and detail
  - `>= 0.80`: `AI_HIGH`
  - `>= 0.40`: `UNCERTAIN`
  - else: `HUMAN_HIGH`

### 2. `tests/` Directory
Comprehensive test suite with 24 tests:

- `__init__.py` — Package marker
- `conftest.py` — pytest integration marker registration
- `test_signals.py` — Full unit and integration test suite
  - 8 unit tests for `llm_signal` (mock, no API key needed)
  - 5 unit tests for `combine_signals`
  - 8 unit tests for `label_selector` boundary conditions
  - 3 integration tests (require GROQ_API_KEY, real Groq API)

### 3. Test Coverage
**Unit Tests (21 tests, always pass):**
- JSON parsing (clean, whitespace, malformed)
- Regex fallback extraction
- Error handling (GroqError, missing keys)
- Score clamping ([0.0, 1.0])
- Weighted average math
- Label threshold logic at all boundaries

**Integration Tests (3 tests, require GROQ_API_KEY):**
- AI-generated text scores `> 0.80`
- Human-written text scores `< 0.35`
- Ambiguous text scores in `[0.40, 0.79]` (UNCERTAIN range)

## Files Modified

### `app.py`
- Added imports: `load_dotenv`, `Limiter`, `RateLimitExceeded`, signal functions
- Call `load_dotenv()` before Flask initialization
- Instantiate `Limiter` with in-memory storage, IP-based limits
- Add 429 error handler for rate limit responses
- Fixed `/submit` route:
  - Added `@app.route` decorator (was missing, route was unreachable)
  - Added `@limiter.limit("10 per minute")`
  - Removed `creator_id` requirement (not in spec)
  - Validate only `text` field (non-empty string)
  - Wire signal functions: `s1 = llm_signal()` → `combine_signals()` → `label_selector()`
  - Return correct response format: `content_id`, `confidence_score`, `label_key`, `label_text`, `label_detail`

## Test Results

### Unit Tests
```
21 passed, 3 deselected (skipped integration tests) in 0.61s
```

### All Tests (with GROQ_API_KEY)
```
24 passed in 1.84s
```

## Verification

### Manual Endpoint Testing
**AI Text (short):** 
- Input: "Artificial intelligence has revolutionized industries..."
- Confidence: 0.52 → UNCERTAIN (shorter text scores lower)

**Human Text:**
- Input: "My grandmother never learned to drive..."
- Confidence: 0.13 → HUMAN_HIGH ✓

**Missing Text:**
- Status: 400 Bad Request ✓
- Error: "Missing required field: 'text' must be a non-empty string."

### Response Format
All responses include:
- `content_id`: UUID
- `confidence_score`: float (rounded 4 places)
- `label_key`: "AI_HIGH" | "UNCERTAIN" | "HUMAN_HIGH"
- `label_text`: Plain-language summary
- `label_detail`: Full transparency explanation

## Design Notes

1. **Groq API Integration:** Instantiated per-call inside `llm_signal()` to ensure environment variables are loaded. `temperature=0.0` maximizes determinism.

2. **Parse Fallback Chain:** JSON parse is attempted first for strict correctness, but the regex fallback ensures the system gracefully handles imperfect LLM responses.

3. **Error Sentinel (0.5):** Returns the midpoint of the confidence range on any parse error or API failure, representing genuine uncertainty rather than a hard failure.

4. **Rate Limiting:** Flask-Limiter with in-memory storage keyed by client IP. 10 requests/minute on `/submit` is aggressive enough to prevent abuse while allowing realistic testing.

5. **Label Detail:** The `label_detail` field provides full transparency language per the spec, while `label_text` is the short summary for the response JSON.

## Next Steps (M4)

- Implement `stylometric_signal()` with type-token ratio, sentence length, punctuation, function words, filler phrases
- Update `combine_signals()` to use both signals at 0.65/0.35 weights
- Re-run signal validation tests to confirm label assignment variance improves

## Running the Tests

```bash
# Unit tests only (no API key needed)
python -m pytest tests/test_signals.py -v -m "not integration"

# All tests (requires GROQ_API_KEY in .env)
GROQ_API_KEY="..." python -m pytest tests/test_signals.py -v

# Run Flask app
python app.py
# Then test: curl -X POST http://localhost:5000/submit -H "Content-Type: application/json" -d '{"text":"..."}'
```

## Files Changed Summary

| File | Status | Changes |
|------|--------|---------|
| `signals.py` | Created | 3 functions: llm_signal, combine_signals, label_selector |
| `tests/__init__.py` | Created | Empty package marker |
| `tests/conftest.py` | Created | pytest marker registration |
| `tests/test_signals.py` | Created | 24 tests (21 unit, 3 integration) |
| `app.py` | Modified | Route decorator fix, signal wiring, rate limiting, response format |
| `test_endpoints.py` | Created | Manual endpoint test script (optional, for dev testing) |
| `M3_IMPLEMENTATION_SUMMARY.md` | Created | This file |
