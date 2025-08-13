import os, tempfile
from fastapi import APIRouter, File, UploadFile
from faster_whisper import WhisperModel

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

model = WhisperModel("small", compute_type="int8")

@router.post("/")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    segments, info = model.transcribe(path, vad_filter=True)
    text = " ".join(seg.text.strip() for seg in segments)
    os.remove(path)
    return {"language": info.language, "duration": info.duration, "transcript": text}