"""Dumb non-LLM baseline for the reference feature.

A regex and a first-line summary. No model, no key, no cost. The point of
shipping this is so "85% accurate" has something to stand next to. If this
file scores within a few points of your LLM on your eval set, the LLM is the
wrong tool for the job and MAKE_IT_YOURS.md wants you to say so.
"""

from __future__ import annotations

import re

from app.feature import ALLOWED_LANGUAGES, SnippetFacts

_LANGUAGE_HINTS = [
    ("sql", (r"\bselect\b", r"\binsert\b", r"\bcreate table\b")),
    ("python", (r"^import ", r"^from \w+ import", r"\bdef \w+\(")),
    ("javascript", (r"\bfunction \w*\(", r"\bconst \w+ =", r"=>")),
    ("shell", (r"^\$ ", r"\bgit \w+", r"\bls \b", r"\|\s*xargs\b", r"\blsof\b")),
    ("rust", (r"\blet \w+ =", r"std::", r"\bfn \w+\(")),
    ("docker", (r"^from\s+\w+", r"\bworkdir\b", r"\bcmd\b")),
    ("nginx", (r"\blocation\b", r"\bproxy_pass\b")),
]


def baseline_extract(body: str) -> SnippetFacts:
    language = "unknown"
    lowered = body.lower()
    for name, patterns in _LANGUAGE_HINTS:
        if any(re.search(pattern, lowered, re.MULTILINE) for pattern in patterns):
            language = name
            break
    if language not in ALLOWED_LANGUAGES:
        language = "unknown"

    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    summary = (first_line[:117] + "...") if len(first_line) > 120 else (first_line or "Empty snippet.")

    tags = [language] if language != "unknown" else []
    contains_credential = bool(
        re.search(r"(?i)\b(password|api[_-]?key|secret|token)\s*[:=]", body)
    )
    return SnippetFacts(
        language=language,
        summary=summary,
        tags=tags,
        contains_credential=contains_credential,
    )
