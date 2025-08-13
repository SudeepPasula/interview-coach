from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from sqlmodel import Session as DBSession, select
from ..db import engine
from ..models import Session as SessionModel, Analysis as AnalysisModel, Question

router = APIRouter(prefix="/sessions", tags=["sessions"])

class StartReq(BaseModel):
    role: str = "SWE"
    question_id: int

@router.post("")
def start_session(req: StartReq):
    with DBSession(engine) as s:
        if not s.get(Question, req.question_id):
            return {"error": "invalid question_id"}
        sess = SessionModel(role=req.role, question_id=req.question_id)
        s.add(sess); s.commit(); s.refresh(sess)
        return {"session_id": sess.id}

class SaveReq(BaseModel):
    session_id: int
    transcript: str
    duration_s: float
    metrics: Dict[str, Any]

@router.post("/save")
def save_analysis(req: SaveReq):
    with DBSession(engine) as s:
        sess = s.get(SessionModel, req.session_id)
        if not sess:
            return {"error": "session not found"}
        sess.duration_s = req.duration_s
        s.add(sess)
        ana = AnalysisModel(session_id=req.session_id, transcript=req.transcript, metrics=req.metrics)
        s.add(ana); s.commit(); s.refresh(ana)
        return {"analysis_id": ana.id}