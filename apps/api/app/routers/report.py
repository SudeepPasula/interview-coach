# apps/api/app/routers/report.py
from fastapi import APIRouter, HTTPException
from sqlmodel import Session as DBSession, select
from ..db import engine
from ..models import Analysis

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/{session_id}")
def get_report(session_id: int):
    # Fetch the latest analysis row for this session
    with DBSession(engine) as db:
        stmt = (
            select(Analysis)
            .where(Analysis.session_id == session_id)
            .order_by(Analysis.created_at.desc())
        )
        row = db.exec(stmt).first()

        if not row:
            raise HTTPException(status_code=404, detail="No analysis for session")

        # Defensive unpacking – avoid KeyErrors / None crashes
        m = row.metrics or {}
        coverage = m.get("coverage") or {}
        filler = m.get("filler") or {}

        return {
            "session_id": session_id,
            "overall": m.get("overall"),
            "wpm": m.get("wpm"),
            "filler_total": filler.get("total", 0),
            "coverage_score": coverage.get("score", 0.0),
            "matched": coverage.get("matched", []),
            "tips": m.get("tips", []),
            "transcript": row.transcript,
            "created_at": row.created_at.isoformat(),  # serialize datetime
        }