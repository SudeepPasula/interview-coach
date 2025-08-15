# apps/api/app/routers/report.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import OperationalError
from sqlmodel import Session as DBSession, select

from .. import db as app_db
from ..models import Analysis

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{session_id}")
def get_report(session_id: int):
    """
    Return the latest analysis JSON for a session.
    Uses app_db.engine at call time so tests can patch it.
    """
    try:
        with DBSession(app_db.engine) as db:
            row = db.exec(
                select(Analysis)
                .where(Analysis.session_id == session_id)
                .order_by(Analysis.created_at.desc())
            ).first()
    except OperationalError as e:
        # In a fresh SQLite test DB, the table may not exist yet
        raise HTTPException(status_code=404, detail="No analysis for session") from e

    if not row:
        raise HTTPException(status_code=404, detail="No analysis for session")

    m = row.metrics or {}
    coverage = m.get("coverage") or {}
    filler = m.get("filler") or {}

    return {
        "session_id": session_id,
        "overall": m.get("overall", 0.0),
        "wpm": m.get("wpm", 0),
        "filler_total": filler.get("total", 0),
        "coverage_score": coverage.get("score", 0.0),
        "matched": coverage.get("matched", []),
        "tips": m.get("tips", []),
        "transcript": row.transcript or "",
        "created_at": row.created_at.isoformat(),
    }
