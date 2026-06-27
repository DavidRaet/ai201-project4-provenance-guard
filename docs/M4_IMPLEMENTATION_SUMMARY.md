# M4 Implementation Summary

## Overview
Milestone 4 is complete. The stylometric signal is implemented in pure Python and fully wired into the submission pipeline. The final confidence score now uses both signals at their designed weights (0.65 LLM / 0.35 stylometric). Label thresholds were also recalibrated based on empirical testing.

## Files Modified

### 1. `signals.py`

Two module-level constant sets were added to drive the stylometric heuristics:

**`_FILLER_PHRASES`** (list of 30 substrings):
Contemporary AI clichés detected via substring match on lowercased text. Curated away from archaic early-LLM patterns toward phrases that current models overuse:
- `"delve into"`, `"in the realm of"`, `"plays a pivotal role"`, `"in today's digital age"`, `"by leveraging"`, `"navigating the complexities"`, `"foster a deeper understanding"`, and 23 others.

**`_AI_FUNCTION_WORDS`** (set of 30 tokens):
Expanded beyond traditional connective adverbs to include AI-favored adjectives that rarely appear in casual human writing:
- Connectives: `"therefore"`, `"however"`, `"albeit"`, `"furthermore"`, `"moreover"`, `"notwithstanding"`, etc.
- AI-favored adjectives: `"pivotal"`, `"multifaceted"`, `"comprehensive"`, `"robust"`, `"holistic"`, `"nuanced"`, `"intricate"`, `"paramount"`, `"tapestry"`, `"commendable"`, `"vibrant"`, `"straightforward"`, and others.

**`stylometric_signal(text: str) -> float`** — new function, placed between `llm_signal` and `combine_signals`:

Five heuristics, each normalized to `[0.0, 1.0]` where 1.0 = AI-like, then averaged equally:

| Feature | Signal direction | Normalization |
|---------|-----------------|---------------|
| Type-token ratio | Higher TTR (diverse formal vocab) → AI | `(ttr - 0.40) / 0.40`, clamped |
| Avg sentence length | Longer → AI; ≥25 words = 1.0, ≤8 = 0.0 | `(avg_len - 8) / 17`, clamped |
| Punctuation density | Moderate range (0.04–0.10 of chars) → AI | 1.0 in range; linear ramp outside |
| Function word frequency | `_AI_FUNCTION_WORDS` tokens ≥5% of words → 1.0 | `ratio / 0.05`, clamped |
| Filler phrase detection | ≥2 matches in `_FILLER_PHRASES` → 1.0 | `count / 2`, clamped |

Edge case: returns `0.5` sentinel if text contains no extractable words.

**`label_selector` thresholds recalibrated** (based on empirical pipeline testing):

| Before (M3) | After (M4) | Label |
|-------------|------------|-------|
| `>= 0.80` | `>= 0.75` | `AI_HIGH` |
| `>= 0.40` | `>= 0.35` | `UNCERTAIN` |
| `< 0.40` | `< 0.35` | `HUMAN_HIGH` |

Rationale: with both signals active, combined scores are higher than the M3 placeholder (`s2=0.0`). The thresholds were pulled down slightly so that genuinely human text lands in `HUMAN_HIGH` rather than being caught in `UNCERTAIN`.

### 2. `app.py`

- Added `stylometric_signal` to the import from `signals`
- In `/submit`, replaced `combine_signals(s1, 0.0)` placeholder with:
  ```python
  llm_sig = llm_signal(text)
  stylo_signal = stylometric_signal(text)
  confidence_score = combine_signals(llm_sig, stylo_signal)
  ```

### 3. `tests/test_signals.py`

- Added `stylometric_signal` to the import
- Added `TestStylometricSignal` class with 7 unit tests (E1–E7):
  - E1: Empty string → 0.5 sentinel
  - E2: Formal AI-like text (fillers + function words + long sentences) → score > 0.5
  - E3: Short casual human text (no AI markers) → score < 0.5
  - E4: Filler-phrase-heavy text scores higher than identical text without fillers
  - E5: Function-word-dense text → score > 0.5
  - E6: Very short sentences suppress sent_len heuristic → score < 0.4
  - E7: Output always in `[0.0, 1.0]` for edge-case inputs
- Updated `TestLabelSelector` boundary tests (C2–C6) to match new thresholds (0.75 / 0.35)

## Test Results

### Unit Tests (no API key needed)
```
28 passed, 3 deselected in 0.32s
```

### Test Breakdown
- `TestLLMSignal` (A1–A8): 8 tests — unchanged, all pass
- `TestCombineSignals` (B1–B5): 5 tests — unchanged, all pass
- `TestLabelSelector` (C1–C8): 8 tests — boundary values updated, all pass
- `TestIntegration` (D1–D3): 3 tests — require `GROQ_API_KEY`, deselected in unit run
- `TestStylometricSignal` (E1–E7): 7 new tests — all pass

## Design Notes

1. **Contemporary filler phrase list:** The original phrase set targeted early LLM patterns ("in conclusion", "furthermore"). The curated list targets what current models (GPT-4-class, Claude, Llama 3) actually overuse — phrases like "plays a pivotal role", "delve into", "in today's digital age", "by leveraging".

2. **`_AI_FUNCTION_WORDS` includes adjectives:** Traditional stylometry uses only connective adverbs as function words. Expanding to AI-favored adjectives ("pivotal", "nuanced", "holistic", etc.) adds a strong signal not captured by the filler phrase list, since these words appear inline and don't form predictable multi-word patterns.

3. **Equal weighting across five heuristics:** Each of the five sub-scores contributes 20% of the final stylometric score. No single feature dominates; a text needs to exhibit multiple AI markers to score high.

4. **Threshold adjustment rationale:** With `s2=0.0` (M3), a 0.9 LLM score yielded `0.65 × 0.9 = 0.585` — UNCERTAIN. With `s2 ≈ 0.6` (M4), the same text yields `0.65 × 0.9 + 0.35 × 0.6 = 0.795` — still UNCERTAIN under the old 0.80 threshold. Lowering to 0.75 ensures clearly AI-generated text crosses into `AI_HIGH`.

5. **TTR direction:** Higher TTR (more unique words) is treated as AI-like, reflecting the formal, non-repetitive vocabulary of LLM output. This is most reliable for longer texts; for short texts, filler phrase and function word features carry more weight.

## Running the Tests

```bash
# Unit tests only (no API key needed)
python -m pytest tests/test_signals.py -v -k "not integration"

# All tests (requires GROQ_API_KEY in .env)
python -m pytest tests/test_signals.py -v

# Manual smoke test — confirm labels differ
python app.py  # terminal 1
# terminal 2:
curl -X POST http://localhost:5000/submit -H "Content-Type: application/json" \
  -d '{"text": "By leveraging holistic frameworks, organizations can navigate the complexities of digital transformation in today'\''s ever-evolving landscape."}'
# Expected: AI_HIGH

curl -X POST http://localhost:5000/submit -H "Content-Type: application/json" \
  -d '{"text": "She woke up tired. Made coffee. Still exhausted. The cat judged her. Why does she stay up so late?"}'
# Expected: HUMAN_HIGH
```

## Files Changed Summary

| File | Status | Changes |
|------|--------|---------|
| `signals.py` | Modified | Added `_FILLER_PHRASES`, `_AI_FUNCTION_WORDS`; added `stylometric_signal()`; recalibrated `label_selector` thresholds to 0.75/0.35 |
| `app.py` | Modified | Import `stylometric_signal`; replace `s2=0.0` placeholder with live stylometric call |
| `tests/test_signals.py` | Modified | Added `stylometric_signal` import; added `TestStylometricSignal` (E1–E7); updated `TestLabelSelector` boundary values |
| `docs/M4_IMPLEMENTATION_SUMMARY.md` | Created | This file |

## Next Steps (M5)

- Implement `POST /appeal` with full validation (400 on missing reasoning, 404 on unknown content_id, 409 on duplicate pending appeal)
- Implement `GET /log` returning all audit entries in chronological order
- Add structured audit log: append-only JSON entries for submissions and appeals
- Add rate limits to `/appeal` (5/min) and `/log` (30/min)
