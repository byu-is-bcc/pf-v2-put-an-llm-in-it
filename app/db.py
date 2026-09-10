"""Storage for the seed snippets service. Finished; not part of the assignment.

SQLite by default so a fresh clone runs with no setup. Set DATABASE_URL to a
Postgres URL when you deploy.

If you did V1, delete this file along with the rest of the seed and attach your
LLM feature to your own application instead.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./snippets.db")

# check_same_thread is a SQLite-only argument and passing it to Postgres is an
# error, so it only goes in when the URL is actually SQLite.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Snippet(Base):
    """One saved piece of text. A title, a body, and free-text tags.

    `tags` is a comma-separated string rather than a related table. That is the
    wrong shape for a real application and the right shape for a seed, because
    the schema is not what this project is about and a join here would cost you
    an hour you should spend on the eval set.

    `language` and `summary` are nullable on purpose. They are the fields the
    reference LLM feature fills in, so an unprocessed snippet has them empty and
    you can tell at a glance which rows the model has touched.
    """

    __tablename__ = "snippets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session():
    """FastAPI dependency. One session per request, closed either way."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def session_scope() -> Session:
    """A session for code that is not inside a request, such as the seeder."""
    return SessionLocal()
