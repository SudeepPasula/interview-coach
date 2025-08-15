# apps/api/app/routers/report_pdf.py
from __future__ import annotations

import io
import os
from datetime import UTC
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pyppeteer import launch
from sqlmodel import Session as DBSession, select

from ..db import get_session
from ..models import Analysis

router = APIRouter(prefix="/report", tags=["report"])

# Resolve templates dir relative to this file: app/templates
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(),
)


async def html_to_pdf(html: str) -> bytes:
    """
    Render HTML to PDF using headless Chromium via pyppeteer.
    - No 'waitUntil' (pyppeteer Page.setContent doesn't support it)
    - Best-effort emulate screen media
    - Extra args for containers (no sandbox / dev-shm usage)
    """
    executable_path = os.getenv("CHROMIUM_PATH")  # let pyppeteer download if None

    browser = None
    try:
        browser = await launch(
            executablePath=executable_path,
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        page = await browser.newPage()
        await page.setContent(html)

        try:
            await page.emulateMedia("screen")  # type: ignore[attr-defined]
        except Exception:
            pass

        try:
            await page.waitForTimeout(120)
        except Exception:
            pass

        pdf_bytes = await page.pdf(
            {
                "format": "A4",
                "printBackground": True,
                "margin": {
                    "top": "20px",
                    "bottom": "20px",
                    "left": "12mm",
                    "right": "12mm",
                },
            }
        )
        return pdf_bytes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF render failed: {e}") from e
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


@router.get(
    "/{session_id}/pdf",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF file"}},
)
async def report_pdf(
    session_id: int,
    db: Annotated[DBSession, Depends(get_session)],
):
    """
    Generate a PDF report for the latest Analysis of a session.
    """
    row = db.exec(
        select(Analysis)
        .where(Analysis.session_id == session_id)
        .order_by(Analysis.created_at.desc())
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="No analysis for session")

    m = row.metrics or {}
    coverage = m.get("coverage") or {}
    filler = m.get("filler") or {}
    tips = m.get("tips") or []

    html = env.get_template("report.html").render(
        session_id=session_id,
        created_at=row.created_at.isoformat(),
        overall=m.get("overall", 0),
        wpm=m.get("wpm", 0),
        filler_total=filler.get("total", 0),
        coverage_score=coverage.get("score", 0.0),
        matched=coverage.get("matched", []),
        transcript=row.transcript or "",
        tips=tips,
    )

    pdf = await html_to_pdf(html)

    # Ensure timestamp is timezone-aware (treat naive as UTC)
    ts_dt = row.created_at
    if ts_dt.tzinfo is None:
        ts_dt = ts_dt.replace(tzinfo=UTC)
    ts = ts_dt.astimezone(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"report-s{session_id}-a{row.id}-{ts}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
