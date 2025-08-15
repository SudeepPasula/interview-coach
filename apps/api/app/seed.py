from sqlmodel import Session as DBSession
from sqlmodel import select

from .db import engine
from .models import Question

SEED = [
    Question(
        role="SWE",
        text="Tell me about a challenging bug you fixed.",
        key_points=[
            "root cause analysis",
            "debugging steps",
            "tools used",
            "impact",
            "lesson learned",
        ],
    ),
    Question(
        role="SWE",
        text="Describe a system you designed.",
        key_points=["requirements", "trade-offs", "scalability", "bottlenecks", "monitoring"],
    ),
    Question(
        role="SWE",
        text="Tell me about a time you improved a process.",
        key_points=["baseline", "change made", "measurement", "impact", "follow-up"],
    ),
]


def run():
    with DBSession(engine) as s:
        for q in SEED:
            exists = s.exec(select(Question).where(Question.text == q.text)).first()
            if not exists:
                s.add(q)
        s.commit()


if __name__ == "__main__":
    run()
