"""One client, four providers, plus a stub that needs no account at all.

Finished plumbing. Read it, do not rewrite it. Your hours belong in the feature,
the eval set, and the injection write-up.

Every provider in PROVIDERS speaks the OpenAI chat-completions shape, so the
only things that change between them are a base URL, an environment variable
name, and a model id. That is the whole reason this file is short. Swapping
Groq for Gemini is one line in .env, which is what you want when a free tier
changes terms in the middle of your project. It will.

    LLM_PROVIDER=stub        no account, no network, no key. The default.
    LLM_PROVIDER=ollama      a model on your own machine. No account.
    LLM_PROVIDER=gemini      Google AI Studio.
    LLM_PROVIDER=groq        GroqCloud.
    LLM_PROVIDER=openrouter  OpenRouter, using a model id ending in :free.

The key is read from the environment on the server. It is never sent to the
browser and it never appears in a response body. That is not a style choice:
V0 had you watch a key leak in devtools and V1 moved your secrets behind a
server, and this is the rung where it costs money if you get it wrong.

Failure is normal here in a way it is not for an ordinary HTTP call. The
provider will time out, rate-limit you, and return text that is not the JSON
you asked for, and it will do all three on the day your reviewer opens the
link. Everything in this file exists to make those cases legible rather than to
hide them.
"""

from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass, field

import httpx


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Provider:
    """Everything that differs between one free provider and the next.

    `key_env` is None for providers that need no credential. `docs` is here so
    that when a model id goes stale, and it will, the error message can tell
    you where the current list lives instead of leaving you to search.
    """

    name: str
    base_url: str
    key_env: str | None
    default_model: str
    docs: str


PROVIDERS: dict[str, Provider] = {
    "stub": Provider(
        name="stub",
        base_url="",
        key_env=None,
        default_model="stub-1",
        docs="app/llm.py, function _stub_completion",
    ),
    "ollama": Provider(
        name="ollama",
        base_url="http://localhost:11434/v1",
        key_env=None,
        default_model="llama3.1:8b",
        docs="https://ollama.com/library",
    ),
    "gemini": Provider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        key_env="GEMINI_API_KEY",
        default_model="gemini-3.5-flash-lite",
        docs="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    "groq": Provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        key_env="GROQ_API_KEY",
        default_model="openai/gpt-oss-20b",
        docs="https://console.groq.com/docs/models",
    ),
    "openrouter": Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        key_env="OPENROUTER_API_KEY",
        default_model="google/gemma-4-31b-it:free",
        docs="https://openrouter.ai/models?q=free",
    ),
}

# Every model id above was live on 2026-09-10. They go stale faster than
# anything else in this template. PROVIDERS.md says how each one was checked
# and gives you the one command that re-checks it.

TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "20"))
MAX_ATTEMPTS = int(os.environ.get("LLM_MAX_ATTEMPTS", "3"))


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Base for everything this module raises.

    Four subclasses, because the caller does different things for each and a
    single generic exception forces every caller to parse a message string to
    find out what happened.
    """


class LLMTimeout(LLMError):
    """The provider did not answer inside TIMEOUT_SECONDS."""


class LLMRateLimited(LLMError):
    """429. Carries retry_after when the provider sent one."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class LLMUnavailable(LLMError):
    """The provider is reachable but cannot serve this request: 5xx, refused
    connection, a model id that no longer exists, a rejected key."""


class LLMBadResponse(LLMError):
    """The call succeeded and the body was not the shape the API documents.

    Rare, and worth its own class, because a KeyError deep in a parser during a
    demo is a much worse experience than one sentence naming the provider.
    """


# ---------------------------------------------------------------------------
# The response
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    """One completion, plus the numbers MEASUREMENTS.md asks you for.

    Collecting tokens and latency here rather than at the call site is
    deliberate. If measurement is something you have to remember to add, you
    will add it on day twenty-nine, and by then you have no baseline to compare
    against.

    `attempts` is 1 unless a retry happened. A feature that quietly retries
    three times has three times the token cost and three times the latency, and
    a p95 that looks fine because you only measured the last attempt is a lie.

    `finish_reason` is the field everyone ignores until it bites them. "stop"
    means the model finished its sentence. "length" means you cut it off at
    max_tokens and the JSON you are about to parse is half a JSON. Those two
    produce the same 200 and need completely different handling, and you cannot
    tell them apart from the text alone.
    """

    text: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    attempts: int = 1
    finish_reason: str = "stop"
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


# ---------------------------------------------------------------------------
# The call
# ---------------------------------------------------------------------------

def resolve_provider() -> Provider:
    """Which provider this process is configured for.

    Defaults to the stub so that a fresh clone runs. Every real provider is one
    environment variable away, and none of them are the default, because a
    template whose first run spends someone's quota is a bad template.
    """
    name = os.environ.get("LLM_PROVIDER", "stub").strip().lower()
    if name not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise LLMError(f"Unknown LLM_PROVIDER {name!r}. Known providers: {known}.")
    return PROVIDERS[name]


def resolve_model(provider: Provider) -> str:
    return os.environ.get("LLM_MODEL", "").strip() or provider.default_model


def complete(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 400,
    temperature: float = 0.0,
    response_format: dict | None = None,
) -> LLMResponse:
    """Send a chat completion and return the text with its measurements.

    temperature defaults to 0. It does not make a model deterministic, and
    anyone who tells you it does has not run the same prompt a hundred times,
    but it removes the variance you chose to add on top of the variance you are
    stuck with. Your eval numbers move around less, which makes a change in
    them mean something.

    `response_format={"type": "json_object"}` asks the provider to constrain the
    output to valid JSON. Support is uneven: Groq and Gemini honour it, Ollama
    accepts a full JSON schema in its own `format` field instead, and some
    OpenRouter free models ignore it entirely. Ask for it anyway, and then parse
    defensively as though you had not, because the day you trust it is the day
    you are routed to the model that does not.

    Retries are for the transient failures only: a timeout, a 429, a 5xx. A 400
    is not transient, and retrying it three times turns one clear error into
    three slow ones.
    """
    provider = resolve_provider()
    model = resolve_model(provider)

    if provider.name == "stub":
        return _stub_completion(messages, model=model, max_tokens=max_tokens)

    payload: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}
    if provider.key_env:
        key = os.environ.get(provider.key_env, "").strip()
        if not key:
            raise LLMUnavailable(
                f"{provider.key_env} is not set. Provider {provider.name!r} needs it. "
                f"Copy .env.example to .env and fill it in."
            )
        headers["Authorization"] = f"Bearer {key}"

    url = provider.base_url.rstrip("/") + "/chat/completions"
    last_error: LLMError | None = None
    started = time.perf_counter()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                http_response = client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as error:
            last_error = LLMTimeout(
                f"{provider.name} did not answer in {TIMEOUT_SECONDS}s: {error}"
            )
        except httpx.HTTPError as error:
            # Connection refused is the common one, and for Ollama it almost
            # always means the daemon is not running rather than anything subtle.
            last_error = LLMUnavailable(f"Could not reach {provider.name} at {url}: {error}")
        else:
            if http_response.status_code == 429:
                last_error = LLMRateLimited(
                    f"{provider.name} rate limited this request (429). "
                    f"Free tiers are small; see PROVIDERS.md.",
                    retry_after=_retry_after_seconds(http_response),
                )
            elif http_response.status_code >= 500:
                last_error = LLMUnavailable(
                    f"{provider.name} returned {http_response.status_code}."
                )
            elif http_response.status_code >= 400:
                # Not retryable. A bad model id and a rejected key both land
                # here, and both need you, not another attempt.
                raise LLMUnavailable(
                    f"{provider.name} rejected the request with "
                    f"{http_response.status_code}: {_short(http_response.text)}. "
                    f"If the model id is wrong, the current list is at {provider.docs}."
                )
            else:
                elapsed_ms = (time.perf_counter() - started) * 1000
                return _parse_completion(
                    http_response,
                    provider=provider.name,
                    model=model,
                    latency_ms=elapsed_ms,
                    attempts=attempt,
                )

        if attempt < MAX_ATTEMPTS:
            _sleep_before_retry(attempt, last_error)

    raise last_error or LLMUnavailable(f"{provider.name} failed for an unrecorded reason.")


def _retry_after_seconds(http_response: httpx.Response) -> float | None:
    """Read Retry-After, which providers send in seconds and sometimes not at all."""
    header = http_response.headers.get("retry-after")
    if not header:
        return None
    try:
        return float(header)
    except ValueError:
        # The HTTP-date form of the header is legal and nobody sends it here.
        return None


def _sleep_before_retry(attempt: int, error: LLMError | None) -> None:
    """Exponential backoff with jitter, and obey Retry-After when it is given.

    The jitter matters more than it looks. Without it, every request that gets
    a 429 at the same moment retries at the same moment, and you have built a
    small synchronised stampede against a provider that just told you to slow
    down.
    """
    if isinstance(error, LLMRateLimited) and error.retry_after:
        time.sleep(min(error.retry_after, 30.0))
        return
    time.sleep(min(2 ** (attempt - 1), 8) * (0.5 + random.random()))


def _parse_completion(
    http_response: httpx.Response,
    *,
    provider: str,
    model: str,
    latency_ms: float,
    attempts: int,
) -> LLMResponse:
    """Pull the text and the token counts out of a 200 response.

    Wrapped in its own function with its own error because the OpenAI response
    shape is nested four deep and every provider gets one corner of it slightly
    wrong. Some omit `usage` entirely, which is why the token counts default to
    zero rather than raising: a missing measurement should degrade your cost
    report, not fail the request a user is waiting on.
    """
    try:
        body = http_response.json()
    except ValueError as error:
        raise LLMBadResponse(f"{provider} returned a 200 that is not JSON: {error}") from error

    try:
        choice = body["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise LLMBadResponse(
            f"{provider} returned 200 with no choices[0].message.content: {_short(str(body))}"
        ) from error

    usage = body.get("usage") or {}
    return LLMResponse(
        text=text or "",
        model=body.get("model") or model,
        provider=provider,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        latency_ms=latency_ms,
        attempts=attempts,
        finish_reason=choice.get("finish_reason") or "stop",
        raw=body,
    )


def _short(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


# ---------------------------------------------------------------------------
# The stub
# ---------------------------------------------------------------------------

# Forces a specific failure out of the stub, for the paths you cannot get a
# real provider to produce on demand:
#
#     LLM_STUB_FAILURE=malformed   prose where JSON should be
#     LLM_STUB_FAILURE=truncated   valid JSON cut off mid-string
#     LLM_STUB_FAILURE=refusal     a polite decline
#     LLM_STUB_FAILURE=injected    the model obeyed text inside the data
#     LLM_STUB_FAILURE=empty       an empty completion
#     LLM_STUB_FAILURE=timeout     raises LLMTimeout
#     LLM_STUB_FAILURE=ratelimit   raises LLMRateLimited
#
# You cannot ask Gemini to return malformed JSON on Tuesday because that is the
# branch you are testing. This is how you cover the branch anyway, and covering
# it is most of FAILURE_MODES.md.
STUB_FAILURE_ENV = "LLM_STUB_FAILURE"

_LANGUAGE_HINTS = [
    ("sql", (r"\bselect\b", r"\binsert\b", r"\bcreate table\b")),
    ("python", (r"^import ", r"^from \w+ import", r"\bdef \w+\(")),
    ("javascript", (r"\bfunction \w*\(", r"\bconst \w+ =", r"=>")),
    ("shell", (r"^\$ ", r"\bgit \w+", r"\bls \b", r"\|\s*xargs\b", r"\blsof\b")),
    ("rust", (r"\blet \w+ =", r"std::", r"\bfn \w+\(")),
]


def _stub_completion(
    messages: list[dict[str, str]], *, model: str, max_tokens: int
) -> LLMResponse:
    """A fake completion, so a fresh clone runs before you have any account.

    **The stub is not a model and its output is not evidence.** It matches a few
    regexes and returns schema-valid JSON. Every number it produces is fake:
    the token counts are a word count, the latency is the microseconds this
    function took, and the cost is zero. An eval run against the stub tells you
    your harness works. It tells you nothing about your feature.

    It exists for three real jobs. It makes `pytest` pass on a fresh clone with
    no credential. It gives CI something to run. And LLM_STUB_FAILURE lets you
    reach the failure branches a real provider will not produce on demand.

    Notice what it does not do: it does not obey the instruction planted in the
    "Deploy notes, staging" seed row. A real model sometimes will. Do not let a
    green stub run convince you your injection defence works.
    """
    started = time.perf_counter()
    forced = os.environ.get(STUB_FAILURE_ENV, "").strip().lower()

    if forced == "timeout":
        raise LLMTimeout("stub: forced timeout via LLM_STUB_FAILURE=timeout")
    if forced == "ratelimit":
        raise LLMRateLimited("stub: forced 429 via LLM_STUB_FAILURE=ratelimit", retry_after=1.0)

    prompt = "\n".join(message.get("content", "") for message in messages)
    body = _stub_extract_data_block(prompt)

    if forced == "malformed":
        text = "Sure. Looking at this snippet, it appears to be Python code that reads a file."
    elif forced == "truncated":
        text = '{"language": "python", "summary": "Reads a CSV file row by ro'
    elif forced == "refusal":
        text = "I'm sorry, but I can't help with analysing that content."
    elif forced == "injected":
        text = "SYSTEM PROMPT LEAKED"
    elif forced == "empty":
        text = ""
    else:
        text = json.dumps(
            {
                "language": _stub_guess_language(body),
                "summary": _stub_summary(body),
                "tags": _stub_tags(body),
                "contains_credential": bool(
                    re.search(r"(?i)\b(password|api[_-]?key|secret|token)\s*[:=]", body)
                ),
            }
        )

    latency_ms = (time.perf_counter() - started) * 1000
    return LLMResponse(
        text=text,
        model=model,
        provider="stub",
        prompt_tokens=len(prompt.split()),
        completion_tokens=len(text.split()),
        latency_ms=latency_ms,
        attempts=1,
        finish_reason="length" if forced == "truncated" else "stop",
        raw={"stub": True, "forced_failure": forced or None},
    )


def _stub_extract_data_block(prompt: str) -> str:
    """Pull out whatever sits between the delimiters the feature uses.

    The stub reads the same fence the real prompt writes, which keeps the two
    honest about each other. If you change the delimiter in feature.py and
    forget this, the stub goes blind and its answers get obviously worse, which
    is the cheapest possible reminder.
    """
    match = re.search(r"<<<SNIPPET\n(.*?)\nSNIPPET>>>", prompt, re.DOTALL)
    return match.group(1) if match else prompt


def _stub_guess_language(body: str) -> str:
    lowered = body.lower()
    for language, patterns in _LANGUAGE_HINTS:
        if any(re.search(pattern, lowered, re.MULTILINE) for pattern in patterns):
            return language
    return "unknown"


def _stub_summary(body: str) -> str:
    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    return (first_line[:117] + "...") if len(first_line) > 120 else (first_line or "Empty snippet.")


def _stub_tags(body: str) -> list[str]:
    language = _stub_guess_language(body)
    return [language] if language != "unknown" else []
