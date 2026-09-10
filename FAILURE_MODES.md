# Failure modes

Every row is a claim about what happens when something goes wrong. Fill in the
**Actual** column by running the request, not by reading the code.

On a fresh clone, `pytest -v tests/test_failure_modes.py` prints a mix of
passes and failures. The failures name the work still left. When the suite is
green, every Expected below should match what you observed.

Force stub failures with `LLM_STUB_FAILURE` — see `.env.example`.

| # | Trigger | Expected | Actual | Where |
|---|---|---|---|---|
| 1 | `POST /snippets/99999/analyze` | 404, body names the missing id | | `main.py` |
| 2 | Burst above per-caller limit | `RateLimited`, `retry_after` > 0 | | `limits.py` |
| 3 | Daily request cap exhausted | `CapReached`, distinct from row 2 | | `limits.py` |
| 4 | `LLM_STUB_FAILURE=malformed` | `FeatureError`, not a raw `JSONDecodeError` | | `feature.py` |
| 5 | `LLM_STUB_FAILURE=injected` | `InjectedOutput`, fail closed | | `feature.py` |
| 6 | Analyze a Python seed snippet | 200; `language` persisted on the row | | `main.py` |
| 7 | `GET /health` | Includes `limits` snapshot | | `main.py` |
| 8 | Body is only whitespace | `EmptyInput` / 400, **no** provider call | `TODO` | `feature.py` |
| 9 | `LLM_STUB_FAILURE=truncated` | `TruncatedOutput` from `finish_reason=length` | `TODO` | `feature.py` |
| 10 | `LLM_STUB_FAILURE=refusal` | 502 whose message names a refusal | `TODO` | `feature.py` |
| 11 | Language outside allowlist | `FeatureError` on schema validation | | `feature.py` |
| 12 | `POST /snippets` with blank title | 422 | | `main.py` |
| 13 | Analyze with a dummy `GEMINI_API_KEY` set | Key does not appear in the response body | | `main.py` |
| 14 | `static/app.js` | No `API_KEY` / `Bearer` / `sk-` literals | | `static/` |

Rows 8–10 are the ones left open in the reference feature on purpose. They are
ordinary, and they are the ones that show up in demos.

When you replace the reference feature, rewrite this table for your feature's
paths. Keep the habit: every ugly case gets a row, and every row gets a test.
