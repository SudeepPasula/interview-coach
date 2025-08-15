# apps/api/app/main.py
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db as app_db  # import module so tests can patch engine if needed
from .routers import analyze_text, jobs, questions, report, report_pdf, sessions, transcribe


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app_db.init_db()
    yield
    # shutdown (nothing to do yet)


app = FastAPI(title="Interview Coach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    routes = [route.path for route in app.routes]
    return {"ok": True, "service": "Interview Coach API", "endpoints": routes}


app.include_router(transcribe.router)
app.include_router(analyze_text.router)
app.include_router(questions.router)
app.include_router(sessions.router)
app.include_router(report.router)
app.include_router(report_pdf.router)
app.include_router(jobs.router)
