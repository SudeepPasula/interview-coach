import os
from sqlmodel import SQLModel, create_engine

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://coach:coach@localhost:5432/coach")
engine = create_engine(DB_URL, echo=False)

def init_db():
    from .models import Question, Session, Analysis
    SQLModel.metadata.create_all(engine)