from fastapi import APIRouter
from pydantic import BaseModel

from ..questions import QUESTIONS
from ..scoring import (
    coverage_score,
    filler_stats,
    overall_score,
    tips_from_metrics,
    words_per_minute,
)

router = APIRouter(prefix="/analyze_text", tags=["analyze"])


class AnalyzeReq(BaseModel):
    transcript: str
    role: str = "SWE"
    question_id: int | None = 1
    duration_s: float = 60.0


@router.post("")
def analyze(req: AnalyzeReq):
    # find key points
    role_qs = QUESTIONS.get(req.role.upper(), [])
    kp = next((q["key_points"] for q in role_qs if q["id"] == req.question_id), [])
    cov = coverage_score(req.transcript, kp)
    fil = filler_stats(req.transcript)
    pace = words_per_minute(req.transcript, req.duration_s)
    tips = tips_from_metrics(cov, fil, pace, kp)
    overall = overall_score(cov, fil, pace)
    return {
        "coverage": cov,
        "filler": fil,
        "wpm": round(pace, 1),
        "tips": tips,
        "overall": overall,
        "question_id": req.question_id,
        "role": req.role,
    }
