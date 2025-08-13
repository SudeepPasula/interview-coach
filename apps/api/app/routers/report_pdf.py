# apps/api/app/routers/report_pdf.py
from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pyppeteer import launch
from sqlmodel import Session as DBSession, select

from ..db import engine
from ..models import Analysis

router = APIRouter(prefix="/report", tags=["report"])

# Resolve templates dir relative to this file: app/templates
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape()
)

async def html_to_pdf(html: str) -> bytes:
    """
    Render HTML to PDF using headless Chromium via pyppeteer.
    """
    executable_path = os.getenv("CHROMIUM_PATH") or None  # optional explicit path

    browser = await launch(
        executablePath=executable_path,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    page = await browser.newPage()
    await page.setContent(html)
    try:
        await page.emulateMedia("screen")
    except Exception:
        pass
    try:
        await page.waitForTimeout(100)
    except Exception:
        pass

    pdf_bytes = await page.pdf({
        "format": "A4",
        "printBackground": True,
        "margin": {"top": "20px", "bottom": "20px", "left": "12mm", "right": "12mm"},
    })
    await browser.close()
    return pdf_bytes


@router.get(
    "/{session_id}/pdf",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF file"}},
)
async def report_pdf(session_id: int):
    """
    Generate a PDF report for the latest Analysis of a session.
    """
    # Fetch latest analysis row for this session
    with DBSession(engine) as db:
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

    # Render HTML via Jinja2
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

    # Use attachment to force a proper download as .pdf in Swagger/browsers
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{session_id}.pdf"'},
    )