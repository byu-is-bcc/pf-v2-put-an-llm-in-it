# V2 — Put an LLM In It

**Portfolio Factory · Development · Practitioner tier · 15 to 25 hours · Extends V1, or standalone with the seed**

> **Prerequisite: [Project 000](https://github.com/byu-is-bcc/pf-000-portfolio-site).** Build your site first. This project ships with an entry on it.

**Hard constraint: free tier only. No credit card.** The providers this template supports are Google AI Studio (Gemini), Groq, OpenRouter `:free` models, and Ollama on your own machine. OpenAI and Anthropic are out of scope here because both ask for payment details up front. Details and verification dates are in `PROVIDERS.md`.

---

## Replace everything above this line with your own README

The template below is what a finished version looks like. Delete the instructions, keep the shape.

---

## What this project is

Add one LLM feature to an application you own. Keep the API key on the server. Measure whether the feature actually works.

That is the whole assignment. A chat bubble is allowed and it is also the most common, least interesting option. Prefer parsing, classification, summarization, semantic search, or natural-language-to-query, and prefer structured JSON output over free-form prose. Getting a model to return schema-valid JSON, and handling it when it does not, is what integration work looks like.

**What you will actually produce:** a live app with one LLM-backed endpoint, an eval set with a stated baseline and a pass rate, a prompt-injection write-up that does not claim victory, and measured cost and latency from real calls. The claim at the top of your finished README has to contain a number a stranger can check.

---

## The claim

> I added an LLM feature to my own application, kept the key off the client, and measured whether the feature actually works.

Finished shape, with your numbers:

> `<feature>` on `<app>`, key server-side only. Eval set of `<N>` cases: `<P>%` pass vs baseline `<B>%`. p50 `<X>` ms, about `$<C>` per request on `<provider>`. Injection attempt documented in `PROMPT_INJECTION.md`.

---

## Start here

```bash
git clone <your-repo-url> && cd <your-repo>
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # defaults to LLM_PROVIDER=stub
uvicorn app.main:app --reload
```

Open **http://localhost:8000/** for the UI and **http://localhost:8000/docs** for the API. The database creates itself and loads twelve snippets on first run. Try `POST /snippets/4/analyze` — it runs against the stub with no account.

```bash
pytest -v tests/test_smoke.py          # must be green
pytest -v                              # mix of green and red on day one
python -m evals.run                    # harness works on five seed cases
python -m evals.run --gate             # red until you have a real eval set
```

---

## About the red X on this repository

Three CI jobs. Two of them are supposed to disagree with smoke until you are done.

**`smoke (must be green)`** proves the scaffold works on the stub: import, seed, health, analyze, UI.

**`failure-modes (red until you finish)`** runs every row of `FAILURE_MODES.md`. A fresh clone is a mix of passes and failures. It goes green when the last TODO in `app/feature.py` is gone and every row's Actual column matches Expected.

**`gates (red until you finish)`** fails while `MAKE_IT_YOURS.md` still has `TODO`, and while the eval gate reports fewer than 20 cases or a pass rate that does not beat the baseline.

A red X on day one on those two jobs means the template is working.

---

## What is here

```
app/
  main.py          snippets CRUD + POST /snippets/{id}/analyze
  feature.py       reference structured-output feature. Replace it.
  llm.py           finished. One client, four free providers, plus stub.
  limits.py        finished. Per-caller rate limit + daily caps.
  db.py, seed.py   finished. Snippets domain, deliberately not a bookstore.
static/            minimal UI. No keys. Talks only to same-origin endpoints.
evals/
  run.py           harness. --baseline and --gate flags.
  baseline.py      regex baseline so "85%" has something to stand next to.
  cases.jsonl      five seed cases. You need twenty or more.
  prices.json      USD-per-million-token table. Free tiers are 0.
tests/
  test_smoke.py           green on day one
  test_failure_modes.py   mix; maps to FAILURE_MODES.md
  test_gates.py           red until MAKE_IT_YOURS and the eval gate pass
MAKE_IT_YOURS.md          feature decision record. Anti-sameness gate.
FAILURE_MODES.md          every ugly path, Expected vs Actual.
PROMPT_INJECTION.md       honest write-up. Do not claim you prevented it.
MEASUREMENTS.md           tokens, cost, latency from real calls.
PROVIDERS.md              free-tier verification notes with dates.
```

`db.py`, `seed.py`, `llm.py`, and `limits.py` are finished and are not the assignment. Your hours belong in the feature, the eval set, the injection write-up, and the measurements.

---

## Your job

**1. Decide the feature.** Open `MAKE_IT_YOURS.md` before you write a prompt. Pick from the menu there. Shipping the reference "classify this snippet" feature unchanged fails the anti-sameness gate on purpose.

**2. Prefer your own V1 app.** The snippets service is a seed for cold entry. If you already built a backend in V1, attach the LLM feature there and delete this domain. Say which path you took in `MAKE_IT_YOURS.md`.

**3. Keep the key on the server.** The browser calls your backend; your backend calls the provider. This is the payoff of a thread that started in V0 when you watched a key leak in devtools. An LLM key is metered. A leaked one is someone else's bill, charged to you.

**4. Set the limits from measurements.** The numbers in `limits.py` ship tiny on purpose. Fill in `MEASUREMENTS.md` first, then set `LLM_REQUESTS_PER_MINUTE`, `LLM_DAILY_REQUEST_CAP`, and `LLM_DAILY_TOKEN_CAP` to values you can defend out loud.

**5. Handle the ugly paths.** Work through `FAILURE_MODES.md`. The stub can force malformed JSON, truncation, refusal, injection, timeout, and 429 via `LLM_STUB_FAILURE` so you can test branches a real provider will not produce on demand.

**6. Build a real eval set.** Twenty or more labeled cases in `evals/cases.jsonl`. Run `python -m evals.run --gate`. It fails until your pass rate beats the regex baseline by at least five points. If it cannot, the LLM is the wrong tool — say so and pick a different feature.

**7. Attempt prompt injection against yourself.** Use the planted seed row, or write a worse one. Record what happened in `PROMPT_INJECTION.md`. Partial mitigations are expected. A claim that you "prevented" prompt injection is a fail.

**8. Deploy on a free host.** Render, Railway, Fly, or Azure App Service. A reviewer needs to hit your live `/docs` without installing anything. Stick to free-tier LLM providers in production too.

**9. Add it to your Project 000 site** with the claim above.

---

## Feature menu

| Feature | Good for | Fails at | Structured output |
|---|---|---|---|
| Parse / extract | Turning messy text into fields | Ambiguous formats, handwriting-as-text | Natural fit |
| Classify / route | Labels, triage, folding into buckets | Fine-grained sentiment, overlapping labels | Natural fit |
| Summarize | Long notes into one sentence | Faithfulness; will invent detail | Possible |
| Semantic search | "Find notes like this" over your data | Exact match; needs embeddings | Partial |
| NL → query | Letting a user ask your DB in English | Injection into the query; wrong joins | Natural fit |
| Chat over your data | Open-ended Q&A | Evaluation, cost, injection surface | Weak fit |

Chat is last on purpose. If you pick it, your eval set and your injection write-up have more work to do, not less.

---

## Free providers only

| Provider | Account | Credit card | Default model in this template | Notes |
|---|---|---|---|---|
| stub | None | No | `stub-1` | Fake. For CI and day one. Not evidence. |
| Ollama | None | No | `llama3.1:8b` | Local. Install from ollama.com. |
| Gemini | Google AI Studio | No for Free tier | `gemini-3.5-flash-lite` | Limits vary; check your dashboard. |
| Groq | GroqCloud | No for Free plan | `openai/gpt-oss-20b` | Org-level rate limits. |
| OpenRouter | OpenRouter | No for `:free` models | `google/gemma-4-31b-it:free` | 50 req/day until you buy credits. |

Verified 2026-09-10. Re-check before you depend on a model id. `PROVIDERS.md` has the commands.

---

## How to verify this

Same list an alumni reviewer will use.

- [ ] Live URL; `/docs` loads without an account
- [ ] LLM calls go through the server; no key in the client, the repo, or response bodies
- [ ] Rate limit and daily cap demonstrated (screenshot or log of a 429 / 503)
- [ ] `FAILURE_MODES.md` Actual column filled from real runs, not from reading the code
- [ ] Eval set of at least 20 cases; `python -m evals.run --gate` exits 0
- [ ] Baseline number reported next to the feature number
- [ ] `MEASUREMENTS.md` has tokens, cost, p50, p95 from a real provider (not the stub)
- [ ] `PROMPT_INJECTION.md` records an attempt and does not claim the problem is solved
- [ ] `MAKE_IT_YOURS.md` has no `TODO`; the feature is not the unchanged seed
- [ ] No secrets in git history

---

## Resume one-liners

Written after you have real numbers.

- Added a structured-extraction endpoint to a personal API, server-side key only, 24-case eval at 88% vs 62% regex baseline, p50 410 ms on Groq free tier.
- Shipped classification over user-submitted notes with per-IP rate limits and a daily token cap, documented a successful prompt-injection attempt and the partial mitigations that remained.
- Replaced an ad-hoc chat prototype with schema-constrained JSON output and a measured cost of $0.00/request on Gemini free tier at 12k tokens/day budgeted.

---

## Who hires for this

**Startups and enterprise SaaS building AI features into existing products.** Named accounts hiring BYU IS students into engineering: **Epic Systems**, **Enzy**, **nCino**, **Redo**, **Acima Credit**, **BambooHR**, **Podium**.

The skill this rung exercises — calling a model from a backend, constraining the output, and proving it works on a held-out set — is closer to what those teams ask a new grad to do than training a model from scratch.

Those names illustrate the kind of work, not a target list. 73% of the companies that hired BYU IS students in the last five years hired exactly one.

---

## Where people get stuck

**"I will just add a chat widget."** You can. Your eval set will be worse, your injection surface will be larger, and your project will look like everyone else's. Read the feature menu again.

**"The stub passes my evals."** The stub is a regex with a JSON wrapper. It proves the harness runs. Switch `LLM_PROVIDER` to a real free provider before you write a number in your README.

**"My pass rate is worse than the baseline."** Then the LLM is not earning its keep on this task. That is a legitimate finding. Change the feature or narrow the schema until the margin is real.

**"I prevented prompt injection."** No you did not. Document what you tried, what still worked against you, and what you refuse to let model output do unsupervised.

**"I need a credit card for the good models."** Not for this project. Stay on the free tier. If a provider changes terms, swap providers — that is why `llm.py` is one client and four base URLs.

---

## License

MIT. The template is yours to modify. The work you do with it is yours.
