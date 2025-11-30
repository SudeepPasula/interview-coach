# Interview Coach

Interview Coach is a full-stack app that helps you practice technical interviews by recording your answer, transcribing it locally, scoring the response, and generating a clean PDF coaching report.

The goal is to make interview prep feel like a structured coaching session rather than talking into the void.

---

## Features

- Record or upload an answer to a software engineering interview question
- Local speech-to-text using `faster-whisper` (no cloud STT dependency)
- Semantic coverage scoring using sentence embeddings (did you hit key points?)
- Filler word and pacing analysis (words per minute, filler counts)
- Overall score and concrete tips based on your metrics
- Downloadable PDF report generated from an HTML/Jinja template via headless Chromium
- Async job pipeline with Redis + RQ so long-running work does not block the API
- Next.js + TypeScript frontend with React Query for job status and results

---

## High-Level Flow

1. User loads a question and starts a session.
2. User records audio in the browser and submits it.
3. The audio is sent to the FastAPI backend and enqueued as a background job.
4. The worker:
   - transcribes the audio with `faster-whisper`
   - scores the response using semantic similarity and heuristics
   - stores the analysis in Postgres
5. The frontend polls the job status. When it finishes, it fetches a JSON report.
6. The user can download a PDF report generated from the stored metrics and transcript.

---

## Architecture

### Backend (FastAPI)

Located in `apps/api/app`.

Key pieces:

- `main.py`  
  Sets up the FastAPI app, CORS, and includes all routers. On startup it initializes the database schema via SQLModel.

- `db.py`  
  Database configuration using SQLModel and SQLAlchemy.  
  - `DATABASE_URL` is read from the environment and defaults to `sqlite:///./dev.db` for local development.
  - In Docker, this points to the Postgres service.

- `models.py`  
  SQLModel models:
  - `Question` – seeded questions and their key points.
  - `Session` – a practice session (role, question, start time, duration).
  - `Analysis` – transcript plus metrics stored as JSON.

- `routers/questions.py`  
  Simple in-memory question bank keyed by role (currently `SWE`), mapped to:
  - `GET /questions` – all questions.
  - `GET /questions/{role}` – questions for a given role.

- `routers/sessions.py`  
  - `POST /sessions` – creates a new session (role + question).
  - `POST /sessions/{session_id}/finalize` – attaches transcript/metrics to a session in the simpler flow.
  - `GET /sessions/{session_id}` – fetches session data.

- `routers/transcribe.py`  
  Synchronous transcription using `faster-whisper`:
  - Loads a `WhisperModel("small", compute_type="int8")` once per process.
  - Exposes helpers to transcribe from a temporary file or raw bytes.
  - Returns language, duration, and transcript text.

- `routers/analyze_text.py`  
  Pure text analysis endpoint:
  - Computes:
    - semantic coverage relative to the question’s `key_points`
    - filler statistics
    - words per minute
    - overall score and tips
  - Uses helpers in `scoring.py`.

- `scoring.py`  
  Implements the scoring logic:
  - Loads a `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")` model.
  - `coverage_score` uses cosine similarity between sentence embeddings and key points.
  - `filler_stats` counts common fillers (`um`, `uh`, `like`, etc.).
  - `words_per_minute` estimates pacing from transcript + duration.
  - `overall_score` combines coverage, fillers, and pace into a single score.
  - `tips_from_metrics` generates human-readable coaching tips based on those metrics.
  - `analyze` is the main helper used by the worker to compute the full metrics dict.

- `routers/report.py`  
  - `GET /report/{session_id}`  
    Looks up the latest `Analysis` row for the session and returns a JSON “flattened” report:
    - overall score
    - words per minute
    - filler totals
    - coverage score and matched key points
    - tips
    - transcript
    - timestamp

- `routers/report_pdf.py`  
  - Jinja2 environment configured to load `apps/api/app/templates/report.html`.
  - `async def html_to_pdf(html: str)` uses Pyppeteer to:
    - launch Chromium (installed in the API Docker image, or detected via `CHROMIUM_PATH`)
    - render the HTML
    - export a PDF (`A4`, with margins and background printing)
  - `GET /report/{session_id}/pdf`  
    - Fetches the latest analysis for the session
    - Renders the HTML template with metrics and transcript
    - Streams the PDF back as an attachment

- `routers/jobs.py` + `tasks.py`  
  Provide the async pipeline:
  - `POST /jobs/enqueue?session_id=...`  
    - Reads the uploaded audio (`multipart/form-data`)
    - Validates size
    - Enqueues `run_full_pipeline` into an RQ queue (`ic-jobs`)
  - `GET /jobs/{job_id}`  
    - Returns job status and, if finished, the metrics.
  - `tasks.py::run_full_pipeline`  
    - `transcribe_bytes` → transcript
    - Loads the `Session` from the database to get role, question, duration
    - Calls `scoring.analyze` to produce metrics
    - Saves an `Analysis` row and returns the metrics dict.

- `worker.py`  
  Lightweight RQ worker process that listens to the `ic-jobs` queue. Used by the `worker` service in Docker Compose.

### Frontend (Next.js + TypeScript)

Located in `apps/web`.

- `app/page.tsx`  
  The main dashboard:
  - Loads a question via `QuestionCard`.
  - Starts a session by calling `POST /sessions`.
  - Accepts audio from `RecorderCard` and enqueues a job via `POST /jobs/enqueue`.
  - Uses `JobStatusCard` (React Query) to poll `GET /jobs/{id}`.
  - When the job is finished, calls `GET /report/{session_id}` and renders the results via `ReportCard`.
  - Provides a link to the API docs (`/docs`) and a “Start New Session” reset button.

- `components/QuestionCard.tsx`  
  Fetches a random SWE question from `/questions/SWE` and displays it.

- `components/RecorderCard.tsx`  
  Simple in-browser audio recorder built on the MediaRecorder API:
  - Handles microphone permission
  - Captures audio chunks and emits a `File` to the parent component
  - Handles unsupported browsers gracefully

- `components/JobStatusCard.tsx`  
  Polls `/jobs/{id}` using React Query:
  - Renders queued/started/finished/failed states
  - Calls an `onFinished` callback when the job reaches `finished`.

- `components/ReportCard.tsx`  
  Renders the JSON report:
  - Overall score with basic color coding
  - Coverage score and matched key points
  - Filler summary and WPM
  - Coaching tips and timestamp
  - Download button linking to `/report/{session_id}/pdf` on the API host

- `lib/api.ts` / `lib/types.ts`  
  Shared Axios instance pointing to `NEXT_PUBLIC_API_BASE` (defaults to `http://127.0.0.1:8000`) and types for `ReportJson` and `JobStatus`.

The frontend uses Tailwind (v4) utility classes and React Query for data fetching and caching.

### Infrastructure

- `apps/api/Dockerfile`  
  - Based on `python:3.11-slim`.
  - Installs system dependencies:
    - `libgomp1` (for `ctranslate2` / `faster-whisper`)
    - `ffmpeg` (audio handling)
    - `fonts-dejavu` (PDF rendering)
    - `curl` (health checks)
    - `chromium` (for Pyppeteer)
  - Installs Python dependencies from `requirements.txt`.
  - Exposes port `8000` and runs Uvicorn.

- `docker-compose.yml`  
  Orchestrates:
  - `db` – Postgres 16
  - `redis` – Redis for RQ
  - `api` – FastAPI app (depends on db and redis)
  - `worker` – RQ worker process
  - `web` – Next.js frontend on port `3000`
  - Volumes:
    - `pgdata` – Postgres data
    - `hf_cache` – Hugging Face / Whisper model cache
    - `pypp_cache` – Pyppeteer Chromium cache

- `.pre-commit-config.yaml` / `ruff.toml`  
  Pre-commit hooks for:
  - whitespace and conflict markers
  - Ruff linting and formatting (`E`, `F`, `B` rules with a few ignores)

---

## Running the Project

### Prerequisites

- Docker and Docker Compose installed
- Reasonable disk space and bandwidth for model downloads:
  - `faster-whisper` model
  - SentenceTransformer model
  - Chromium for Pyppeteer (if not already installed in the container)

### Quickstart (Recommended)

From the repo root:

```bash
docker compose up --build
