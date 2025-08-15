# apps/api/tests/test_api_basic.py
from __future__ import annotations
import os
import tempfile
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

# import the app and modules we’ll patch
from app.main import app
import app.db as app_db
from app.models import Question, Analysis
from app.routers import report_pdf as report_pdf_router


@contextmanager
def temp_sqlite_engine():
    # temp file instead of :memory: so multiple connections can see the same DB
    fd, path = tempfile.mkstemp(prefix="ic_test_", suffix=".db")
    os.close(fd)
    try:
        engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
        yield engine
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@pytest.fixture(scope="session")
def client():
    # set up a clean SQLite DB and patch the global engine used by the app
    with temp_sqlite_engine() as engine:
        # replace the app’s engine
        app_db.engine = engine  # monkeypatch the module global

        # create tables
        SQLModel.metadata.create_all(engine)

        # seed a couple of questions
        from sqlmodel import Session as DBSession

        with DBSession(engine) as db:
            db.add_all(
                [
                    Question(
                        id=1,
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
                        id=2,
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
            db.commit()

        # stub out the heavy PDF call so tests don’t need Chromium
        async def _fake_html_to_pdf(html: str) -> bytes:
            return b"%PDF-1.4\n% stub test pdf\n"

        report_pdf_router.html_to_pdf = _fake_html_to_pdf  # patch

        with TestClient(app) as c:
            yield c


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_questions(client: TestClient):
    r = client.get("/questions/SWE")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 2
    assert data[0]["role"] == "SWE"
    assert "key_points" in data[0]


def test_create_session_and_report_json(client: TestClient):
    # create session
    r = client.post("/sessions", json={"role": "SWE", "question_id": 1})
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # with no analysis yet, /report/{id} should 404
    r = client.get(f"/report/{session_id}")
    assert r.status_code == 404

    # insert a minimal Analysis row so report endpoint returns data
    from sqlmodel import Session as DBSession

    with DBSession(app_db.engine) as db:
        db.add(
            Analysis(
                session_id=session_id,
                transcript="short transcript for tests",
                metrics={
                    "overall": 0.9,
                    "wpm": 150,
                    "filler": {"total": 0},
                    "coverage": {"score": 0.8, "matched": ["root cause analysis"]},
                    "tips": [],
                },
            )
        )
        db.commit()

    r = client.get(f"/report/{session_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == session_id
    assert body["overall"] == 0.9
    assert body["coverage_score"] == 0.8
    assert body["matched"] == ["root cause analysis"]


def test_report_pdf_streams_pdf(client: TestClient):
    # create session + analysis
    r = client.post("/sessions", json={"role": "SWE", "question_id": 1})
    session_id = r.json()["session_id"]

    from sqlmodel import Session as DBSession

    with DBSession(app_db.engine) as db:
        db.add(
            Analysis(
                session_id=session_id,
                transcript="pdf test transcript",
                metrics={
                    "overall": 0.7,
                    "wpm": 140,
                    "filler": {"total": 2},
                    "coverage": {"score": 0.6, "matched": []},
                    "tips": ["tip1"],
                },
            )
        )
        db.commit()

    # should return our stubbed PDF bytes
    r = client.get(f"/report/{session_id}/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert b"%PDF" in r.content
