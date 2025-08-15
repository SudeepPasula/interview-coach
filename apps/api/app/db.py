# apps/api/app/db.py
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine, select

from .models import Question

# Pick DB URL:
# - In prod/docker set DATABASE_URL=postgresql://...
# - Locally without docker this falls back to a file-based SQLite DB (no server needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# SQLite needs a special arg; Postgres does not.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db(seed: bool = True) -> None:
    """
    Create tables on the current engine and optionally seed baseline data.
    Designed to be safe in tests: if tests override the engine via dependency
    injection, they won't call this implicitly.
    """
    SQLModel.metadata.create_all(engine)

    if not seed:
        return

    # Only seed if empty for the role "SWE"
    with Session(engine) as s:
        already = s.exec(select(Question).where(Question.role == "SWE")).first()
        if already:
            return

        s.add_all(
            [
                Question(
                    role="SWE",
                    text="Tell me about a challenging bug you fixed.",
                    key_points=[
                        "root cause analysis",
                        "debugging steps",
                        "tools used",
                        "impact",
                        "lesson learned",
                    ],
                ),
                Question(
                    role="SWE",
                    text="Describe a system you designed.",
                    key_points=[
                        "requirements",
                        "trade-offs",
                        "scalability",
                        "bottlenecks",
                        "monitoring",
                    ],
                ),
            ]
        )
        s.commit()


def get_session() -> Iterator[Session]:
    """
    FastAPI dependency for DB access.
    Tests can override this with an in-memory engine/session.
    """
    with Session(engine) as session:
        yield session


# Optional: convenience context manager for scripts
@contextmanager
def session_scope() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
