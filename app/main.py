"""V2 — Put an LLM In It.

A small snippets service plus one reference LLM feature that classifies and
summarizes a snippet into structured JSON. The CRUD is finished seed so a cold
entrant has somewhere to attach a feature. The assignment is the feature, the
eval set, the injection write-up, and the measurements — not this file.

If you did V1, delete the snippets domain and wire your feature into your own
app. Keep the LLM call on the server. The key never reaches the browser.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
UI:   http://localhost:8000/
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import Snippet, get_session, init_db
from app.feature import FeatureError, extract_facts
from app.limits import CapReached, RateLimited, caller_id, limiter
from app.llm import resolve_model, resolve_provider
from app.seed import seed_if_empty

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_if_empty()
    yield


app = FastAPI(
    title="Snippets + LLM",
    description=(
        "Portfolio Factory V2 seed. A notes/snippets service in a non-bookstore "
        "domain, plus one reference structured-output LLM feature. Replace the "
        "feature. Prefer your own V1 app if you have one."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SnippetIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=0, max_length=20_000)
    tags: str = Field(default="", max_length=200)


class SnippetOut(BaseModel):
    id: int
    title: str
    body: str
    tags: str
    language: str | None = None
    summary: str | None = None

    model_config = {"from_attributes": True}


class AnalyzeOut(BaseModel):
    snippet_id: int
    language: str
    summary: str
    tags: list[str]
    contains_credential: bool
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    attempts: int
    finish_reason: str


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health(db: Session = Depends(get_session)) -> dict:
    """Liveness plus seed count plus current spend snapshot."""
    count = db.scalar(select(func.count()).select_from(Snippet)) or 0
    provider = resolve_provider()
    return {
        "status": "ok",
        "snippets": count,
        "provider": provider.name,
        "model": resolve_model(provider),
        "limits": limiter.snapshot(),
    }


# ---------------------------------------------------------------------------
# Snippets CRUD — finished seed, not the assignment
# ---------------------------------------------------------------------------

@app.get("/snippets", response_model=list[SnippetOut], tags=["snippets"])
def list_snippets(db: Session = Depends(get_session)) -> list[Snippet]:
    """All snippets. No pagination on purpose — that was V1's problem."""
    return list(db.scalars(select(Snippet).order_by(Snippet.id)).all())


@app.get("/snippets/{snippet_id}", response_model=SnippetOut, tags=["snippets"])
def get_snippet(snippet_id: int, db: Session = Depends(get_session)) -> Snippet:
    snippet = db.get(Snippet, snippet_id)
    if snippet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No snippet {snippet_id}.")
    return snippet


@app.post(
    "/snippets",
    response_model=SnippetOut,
    status_code=status.HTTP_201_CREATED,
    tags=["snippets"],
)
def create_snippet(payload: SnippetIn, db: Session = Depends(get_session)) -> Snippet:
    snippet = Snippet(title=payload.title, body=payload.body, tags=payload.tags)
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet


@app.delete("/snippets/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["snippets"])
def delete_snippet(snippet_id: int, db: Session = Depends(get_session)) -> Response:
    snippet = db.get(Snippet, snippet_id)
    if snippet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No snippet {snippet_id}.")
    db.delete(snippet)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# The LLM endpoint — key stays on the server
# ---------------------------------------------------------------------------

@app.post(
    "/snippets/{snippet_id}/analyze",
    response_model=AnalyzeOut,
    tags=["llm"],
)
def analyze_snippet(
    snippet_id: int,
    request: Request,
    db: Session = Depends(get_session),
) -> AnalyzeOut:
    """Run the reference feature on one snippet. Persist language and summary.

    Rate-limited and capped before any token is spent. On success the usage is
    recorded against the daily token cap. The browser never sees the API key;
    this handler is the whole reason the call is not a fetch() from static JS.
    """
    snippet = db.get(Snippet, snippet_id)
    if snippet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No snippet {snippet_id}.")

    try:
        limiter.check(caller_id(request))
    except RateLimited as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(error),
            headers={"Retry-After": str(int(error.retry_after) or 1)},
        ) from error
    except CapReached as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
            headers={"Retry-After": str(int(error.resets_in) or 60)},
        ) from error

    try:
        result = extract_facts(snippet.body)
    except FeatureError as error:
        raise HTTPException(error.status_code, detail=str(error)) from error

    limiter.record_usage(result.llm.total_tokens)

    snippet.language = result.facts.language
    snippet.summary = result.facts.summary
    # Keep human tags; append model tags that are new.
    existing = {t.strip() for t in snippet.tags.split(",") if t.strip()}
    merged = list(existing)
    for tag in result.facts.tags:
        if tag not in existing:
            merged.append(tag)
    snippet.tags = ",".join(merged)
    db.commit()

    return AnalyzeOut(
        snippet_id=snippet.id,
        language=result.facts.language,
        summary=result.facts.summary,
        tags=result.facts.tags,
        contains_credential=result.facts.contains_credential,
        provider=result.llm.provider,
        model=result.llm.model,
        prompt_tokens=result.llm.prompt_tokens,
        completion_tokens=result.llm.completion_tokens,
        latency_ms=round(result.llm.latency_ms, 2),
        attempts=result.llm.attempts,
        finish_reason=result.llm.finish_reason,
    )


# ---------------------------------------------------------------------------
# Minimal UI — static files, no key material
# ---------------------------------------------------------------------------

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="static/index.html missing.")
    return FileResponse(index_path)
