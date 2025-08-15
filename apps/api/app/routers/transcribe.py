# apps/api/app/routers/transcribe.py
from __future__ import annotations

import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

# Load once per process (API & worker each keep their own)
# Keep your choices: "small" + int8
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("small", compute_type="int8")
    return _model


def _transcribe_path(path: str) -> tuple[str, float, str]:
    """
    Internal helper: given a filesystem path, return (language, duration, text).
    """
    model = _get_model()
    segments, info = model.transcribe(path, vad_filter=True)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return info.language, float(info.duration or 0.0), text


def transcribe_bytes(data: bytes, filename: str | None = None) -> str:
    """
    Public helper for background jobs: transcribe raw audio bytes to text.
    Writes to a temp file (keeps parity with your current path-based call).
    """
    suffix = os.path.splitext(filename or "")[-1] or ".webm"
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.flush()
        tmp.close()
        _lang, _dur, text = _transcribe_path(tmp.name)
        return text
    finally:
        if tmp is not None:
            try:
                os.remove(tmp.name)
            except OSError:
                pass


@router.post("/")
async def transcribe(
    file: Annotated[UploadFile, File(...)],
):
    try:
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Empty file")

        # Reuse the same temp-file path flow to keep behavior identical
        suffix = os.path.splitext(file.filename or "")[-1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(payload)
            path = tmp.name

        try:
            language, duration, text = _transcribe_path(path)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        return {"language": language, "duration": duration, "transcript": text}
    except HTTPException as e:
        # Preserve original HTTPExceptions
        raise e
    except Exception as e:
        # Chain to make debugging clearer (ruff B904)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}") from e
