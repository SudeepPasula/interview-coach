from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import transcribe, analyze_text, questions, sessions, report
from .db import init_db

app = FastAPI(title="Interview Coach API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

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