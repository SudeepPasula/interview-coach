from typing import Any

from sqlmodel import Session as DBSession

from .db import engine
from .models import Analysis
from .routers.transcribe import transcribe_bytes
from .scoring import analyze  # whatever function you use now to score


def run_full_pipeline(session_id: int, audio_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    Background job: transcribe -> analyze -> save Analysis row.
    Returns metrics dict.
    """
    # 1) Transcribe (reuse your current transcribe logic; keep it pure)
    # from .whisper_util import transcribe_bytes  # if you have it split
    # transcript = transcribe_bytes(audio_bytes, filename)
    # If you only have a file-based transcriber, write temp file then call it.
    # For now, we'll assume you can call your existing transcriber here:
    # refactor to expose a helper
    transcript = transcribe_bytes(audio_bytes, filename)

    # 2) Analyze
    # You’ll need role/question_id/duration; simplest is to recompute duration from transcript or pass them in.
    # For now, stub duration=60 and role/question_id from session
    from .models import Question
    from .models import Session as SessionModel

    with DBSession(engine) as s:
        sess = s.get(SessionModel, session_id)
        if not sess:
            raise RuntimeError("Session not found")
        q = s.get(Question, sess.question_id)
        metrics = analyze(
            transcript, role=sess.role, key_points=q.key_points, duration_s=sess.duration_s or 60
        )

        # 3) Save Analysis row
        row = Analysis(session_id=session_id, transcript=transcript, metrics=metrics)
        s.add(row)
        s.commit()
        s.refresh(row)

    return metrics
