# Measurements

Guessed numbers do not belong in a README claim. Fill this in from real calls
against a real free-tier provider. The stub's token counts are word counts and
its latency is the time to run a regex. Do not paste stub numbers here.

```bash
# After setting LLM_PROVIDER and a key in .env:
python -m evals.run
```

The harness prints total tokens, estimated USD (0 on free tiers), p50, and p95.

---

## Setup

| | |
|---|---|
| Provider | `TODO` |
| Model | `TODO` |
| Date measured | `TODO` |
| Case file | `evals/cases.jsonl` (`TODO` cases) |

---

## Per-request (median over the eval set)

| Metric | Value |
|---|---|
| Prompt tokens | `TODO` |
| Completion tokens | `TODO` |
| Total tokens | `TODO` |
| Cost USD (from `evals/prices.json`) | `TODO` |
| Latency p50 (ms) | `TODO` |
| Latency p95 (ms) | `TODO` |

---

## Limits you can defend

Work backwards from budget. On a free tier the dollar budget is zero, so the
binding constraint is the provider's daily request or token limit minus the
headroom you want for your own eval runs.

| Setting | Value | Why |
|---|---|---|
| `LLM_REQUESTS_PER_MINUTE` | `TODO` | |
| `LLM_BURST` | `TODO` | |
| `LLM_DAILY_REQUEST_CAP` | `TODO` | |
| `LLM_DAILY_TOKEN_CAP` | `TODO` | |

Then set them in `.env` or in `app/limits.py`. The placeholders ship tiny so an
unconfigured deploy throttles instead of spending.

---

## Honest limits of the limiter

The counters are in-process memory. They reset when the service sleeps or
restarts, and each replica has its own copy. Say that in your README. A shared
store is the real fix and is out of scope here.
