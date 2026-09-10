# Providers

Free tier only. No credit card. That is a hard constraint for this project.

Model ids go stale faster than anything else in this template. Every default
below was checked on **2026-09-10**. Re-check before you publish a number that
depends on one.

```bash
# OpenRouter: list ids ending in :free
curl -s https://openrouter.ai/api/v1/models | python3 -c \
  "import sys,json; print('\n'.join(m['id'] for m in json.load(sys.stdin)['data'] if m['id'].endswith(':free')))"

# Ollama: local tags
ollama list

# Groq / Gemini: open the console pages linked below; they require an account
# and show the limits for your project, which is the only authoritative view.
```

---

## stub (default)

No account, no network, no key. Returns schema-shaped JSON from a few regexes.

**Not evidence.** An eval run against the stub tells you the harness works. It
tells you nothing about your feature. CI uses it so a fresh clone does not need
credentials.

Force failure branches with `LLM_STUB_FAILURE` — see `.env.example`.

---

## Ollama — local, no account

| | |
|---|---|
| Account | None |
| Credit card | No |
| Cost | $0. Electricity and disk. |
| Default model | `llama3.1:8b` |
| Base URL | `http://localhost:11434/v1` |
| Docs | https://ollama.com/library |

Install from [ollama.com](https://ollama.com), then `ollama pull llama3.1:8b`.
The daemon must be running or `llm.py` raises `LLMUnavailable` with a
connection error.

Verified 2026-09-10: local daemon answered `/api/version` with `0.33.3`. No
API key is required for the OpenAI-compatible endpoint.

---

## Google AI Studio (Gemini) — Free tier

| | |
|---|---|
| Account | Google account at [aistudio.google.com](https://aistudio.google.com) |
| Credit card | **Not required** for the Free usage tier |
| Cost on Free tier | $0 for eligible models (input/output listed as "Free of charge") |
| Default model | `gemini-3.5-flash-lite` |
| Base URL | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Key env | `GEMINI_API_KEY` |
| Docs | https://ai.google.dev/gemini-api/docs/pricing |
| Rate limits | https://ai.google.dev/gemini-api/docs/rate-limits |

**What we verified on 2026-09-10:**

- Pricing page lists a Free Tier column with "Free of charge" for
  `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` (among others).
- Rate-limits page states Free tier qualifies with an "Active project or free
  trial," and that **exact RPM/RPD numbers are no longer published as a fixed
  table**. Limits are per project and visible in AI Studio at
  [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit).
  "Specified rate limits are not guaranteed."
- Free-tier prompts may be used to improve Google products; paid tier opts out.
  Say so in your README if that matters for your data.

We did **not** call Gemini live in this template build (no key in the
environment). Do not treat the default model id as permanently free — re-check
the pricing page when you start.

---

## GroqCloud — Free plan

| | |
|---|---|
| Account | [console.groq.com](https://console.groq.com) |
| Credit card | **Not required** for the Free plan |
| Cost on Free plan | $0; gated by rate limits, not a dollar budget |
| Default model | `openai/gpt-oss-20b` |
| Base URL | `https://api.groq.com/openai/v1` |
| Key env | `GROQ_API_KEY` |
| Docs | https://console.groq.com/docs/models |
| Rate limits | https://console.groq.com/docs/rate-limits |

**What we verified on 2026-09-10:**

- GroqCloud marketing and docs describe a Free plan for building and testing.
- Official rate-limits page shows per-model RPM/RPD/TPM and states limits apply
  at the **organization** level, not per key. Creating more keys does not
  multiply quota.
- Published figures for `openai/gpt-oss-20b` on that page (snapshot): 30 RPM,
  1K RPD, 8K TPM, 200K TPD. Confirm on your own limits page; they change.

We did **not** call Groq live (no key). Some older Llama ids cited in blog
posts are no longer on the free catalog — prefer the console's current list.

---

## OpenRouter — `:free` model variants

| | |
|---|---|
| Account | [openrouter.ai](https://openrouter.ai) |
| Credit card | **Not required** to use `:free` models at $0 balance |
| Cost | $0 on `:free` ids, subject to request caps |
| Default model | `google/gemma-4-31b-it:free` |
| Base URL | `https://openrouter.ai/api/v1` |
| Key env | `OPENROUTER_API_KEY` |
| Docs | https://openrouter.ai/docs/api/reference/limits |

**What we verified on 2026-09-10:**

- Live `GET https://openrouter.ai/api/v1/models` returned **19** model ids
  ending in `:free`, including `google/gemma-4-31b-it:free` and
  `google/gemma-4-26b-a4b-it:free`.
- Official limits docs: for free-model variants, **20 requests/minute**; **50
  requests/day** if lifetime credits purchased are under $10; **1,000
  requests/day** after at least $10 in lifetime credit purchases. Buying
  credits is optional and is **not** required for this project — stay on the
  50/day cap if you do not want a card on file.
- A negative credit balance can break even free models (402). Keep balance at
  zero or above.
- Failed requests still count toward the daily free-model quota.

---

## Providers that are out of scope

OpenAI and Anthropic both require payment details before useful API access.
Do not use them for this project. If you already have a key from elsewhere,
still prefer a no-card free tier here so the portfolio artifact matches the
constraint the program publishes.

---

## Switching

```bash
# .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
# optional:
# LLM_MODEL=gemini-3.1-flash-lite
```

One client in `app/llm.py`. Changing providers is an environment variable, not
a rewrite. That is intentional: free-tier terms move, and you should be able
to move with them in one line.
