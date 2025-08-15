# apps/api/app/models.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: str
    text: str
    # Cross-dialect JSON (works in SQLite tests and Postgres in Docker)
    key_points: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: str
    question_id: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    duration_s: float = 0.0


class Analysis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int
    transcript: str
    # Nested metrics dict stored as JSON
    metrics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
