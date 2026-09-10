"""Smoke tests. Must stay green on a fresh clone.

Proves the scaffold works: app imports, database initializes, seed loads,
/health answers, and /analyze works against the stub with no API key.
"""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["LLM_PROVIDER"] = "stub"
os.environ.pop("LLM_STUB_FAILURE", None)

from app.db import Base, engine, init_db  # noqa: E402
from app.limits import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import SNIPPETS, seed_if_empty  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    init_db()
    seed_if_empty()
    # Fresh limiter state so smoke runs do not trip the daily cap.
    limiter._day_requests = 0
    limiter._day_model_tokens = 0
    limiter._buckets.clear()
    with TestClient(app) as c:
        yield c


def test_health_reports_seed_count(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["snippets"] == len(SNIPPETS)
    assert body["provider"] == "stub"


def test_list_snippets(client):
    r = client.get("/snippets")
    assert r.status_code == 200
    assert len(r.json()) == len(SNIPPETS)


def test_analyze_python_snippet_with_stub(client):
    # Seed row 4 is "Read a CSV without pandas"
    r = client.post("/snippets/4/analyze")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["language"] == "python"
    assert body["provider"] == "stub"
    assert "prompt_tokens" in body
    assert body["latency_ms"] >= 0


def test_ui_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Snippets" in r.text
