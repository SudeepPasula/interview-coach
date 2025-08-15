FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies:
# - libgomp1: required by ctranslate2 / faster-whisper
# - ffmpeg: audio handling
# - fonts-dejavu: for PDF text rendering
# - curl: used by container healthcheck
# - chromium: headless browser for PDF (pyppeteer will use this)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    ffmpeg \
    fonts-dejavu \
    curl \
    chromium \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
COPY app ./app
COPY worker.py ./worker.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
