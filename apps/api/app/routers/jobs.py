from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from redis import Redis
from rq import Queue
from rq.job import Job

# Optional retry support (available on some RQ versions, not on 2.4.1)
try:
    from rq.retry import Retry  # may not exist on your version
except Exception:
    Retry = None  # type: ignore[assignment]

from ..tasks import run_full_pipeline

router = APIRouter(prefix="/jobs", tags=["jobs"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis.from_url(REDIS_URL)
q = Queue("ic-jobs", connection=redis, default_timeout=900)  # 15 min

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/enqueue")
async def enqueue_job(
    session_id: int,
    file: Annotated[UploadFile, File(...)],
):
    blob = await file.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(blob) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (> {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)",
        )

    enqueue_kwargs = {
        "description": f"session:{session_id} file:{file.filename}",
    }
    # Add retry only if supported by this RQ version
    if Retry is not None:
        enqueue_kwargs["retry"] = Retry(max=3, interval=[5, 15, 60])

    job = q.enqueue(
        run_full_pipeline,
        session_id,
        blob,
        file.filename or "audio.webm",
        **enqueue_kwargs,
    )

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.get_id(),
            "enqueued": True,
            "poll_url": f"/jobs/{job.get_id()}",
        },
    )


@router.get("/{job_id}")
def job_status(job_id: str):
    try:
        job: Job = Job.fetch(job_id, connection=redis)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found") from e

    payload: dict[str, object] = {
        "id": job.get_id(),
        "status": job.get_status(),  # queued|started|deferred|finished|failed
        "enqueued_at": getattr(job, "enqueued_at", None),
        "started_at": getattr(job, "started_at", None),
        "ended_at": getattr(job, "ended_at", None),
        "description": getattr(job, "description", None),
        "ttl": job.ttl,
    }
    if job.is_finished:
        payload["result"] = job.result
    elif job.is_failed:
        payload["error"] = (job.exc_info or "")[-800:]
    return payload
