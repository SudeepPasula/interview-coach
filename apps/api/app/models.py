from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any

from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    text: str
    # store list of strings in Postgres JSONB
    key_points: list[str] = Field(default_factory=list, sa_column=Column(JSONB))


class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    question_id: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    duration_s: float = 0.0


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int
    transcript: str
    # store nested metrics dict in Postgres JSONB
    metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)