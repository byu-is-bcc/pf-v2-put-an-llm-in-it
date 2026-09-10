# Make it yours

**Commit this file with the rest of the project. It is part of the deliverable.**

This is a decision record, not a set of instructions. Four questions, answered in
writing before you call V2 finished.

The risk on this rung is severe: every student ships the same chat bubble on the
same snippets seed with the same prompt. Writing the answers down is what turns
a default into a decision. Shipping the reference feature unchanged is a visible
fail on the anti-sameness gate below, and on `tests/test_gates.py`.

None of these need to be long. Two or three sentences each. They need to be
true.

---

## 1. Which application

The intended path is the app you built in V1. The snippets service in this repo
is a seed for cold entry, in a different domain on purpose so it cannot be used
as an answer key for V1's bookstore.

> **I am attaching the LLM feature to:**
> `TODO`   *(my V1 app at \<url or path\> / the snippets seed / something else)*
>
> **If the seed: why I am not using a V1 app:**
> `TODO`

---

## 2. Which feature, and what I rejected

Pick one. Name at least one option you considered and rejected, and why.

| Feature | One-line fit |
|---|---|
| Parse / extract into fields | Unstructured text → schema |
| Classify / route | Label or bucket an input |
| Summarize | Long → short, with a length cap |
| Semantic search | Retrieve over your own data |
| NL → query | English → a constrained query |
| Chat over your data | Allowed; highest eval and injection burden |

> **The feature I am building:**
> `TODO`
>
> **I rejected:**
> `TODO`
>
> **Because:**
> `TODO`

---

## 3. Why an LLM, not a rule or a regex

This is the question that carries the most weight. If `evals/baseline.py` (or
your equivalent) scores within five points of your feature on your own eval
set, the honest answer is that the LLM is the wrong tool. Say so and change the
feature. An interviewer who has shipped this work will ask exactly this.

> **What a non-LLM approach gets right, and where it fails:**
> `TODO`
>
> **Baseline pass rate on my eval set:**
> `TODO`
>
> **Feature pass rate on the same set:**
> `TODO`
>
> **The margin, and why it is worth the cost and the failure modes:**
> `TODO`

---

## 4. What success looks like in a number

One number a stranger can re-check from this repository. Not "it works." Not
"users liked it."

> **The number I am putting in my README claim:**
> `TODO`
>
> **The command or file that produces it:**
> `TODO`

---

## The anti-sameness gate

You are not done if any of these are still true:

1. This file still has unanswered placeholders (the ones marked for you to replace).
2. The live feature is still the unchanged reference classify/summarize path in
   `app/feature.py` on the snippets seed, with no decision recorded above.
3. Your README claim has no eval number next to a baseline number.
4. `PROMPT_INJECTION.md` says you prevented prompt injection.

Any one of those alone can be fine when it is a deliberate, written choice
(for example, you kept structured extraction but moved it onto your own V1
domain and rewrote the schema). All four means no decision was made.

`pytest -v tests/test_gates.py` checks the mechanical half of (1) and the eval
gate behind (3). It cannot check whether your reasoning is any good. That is
what a reviewer reads this file for.
