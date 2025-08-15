# apps/api/app/routers/sessions.py
from __future__ import annotations

from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session as DBSession

from ..db import get_session
from ..models import Analysis as AnalysisModel
from ..models import Question
from ..models import Session as SessionModel

router = APIRouter(prefix="/sessions", tags=["sessions"])


class StartReq(BaseModel):
    role: str = "SWE"
    question_id: int


@router.post("", response_model=dict)
def start_session(
    req: StartReq,
    s: Annotated[DBSession, Depends(get_session)],
):
    """
    Create a new interview session for a given role & question.
    """
    # Ensure the question exists
    if not s.get(Question, req.question_id):
        raise HTTPException(status_code=400, detail="invalid question_id")

    sess = SessionModel(role=req.role, question_id=req.question_id)
    s.add(sess)
    s.commit()
    s.refresh(sess)
    return {"session_id": sess.id}


class SaveReq(BaseModel):
    session_id: int
    transcript: str
    duration_s: float
    metrics: dict[str, Any]


@router.post("/save", response_model=dict)
def save_analysis(
    req: SaveReq,
    s: Annotated[DBSession, Depends(get_session)],
):
    """
    Persist an analysis row and update session duration.
    """
    sess = s.get(SessionModel, req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    # Update session stats
    sess.duration_s = req.duration_s
    s.add(sess)

    # Save analysis
    ana = AnalysisModel(
        session_id=req.session_id,
        transcript=req.transcript,
        metrics=req.metrics,
    )
    s.add(ana)
    s.commit()
    s.refresh(ana)

    return {"analysis_id": ana.id}
