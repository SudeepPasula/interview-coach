# apps/api/app/routers/questions.py

from fastapi import APIRouter

router = APIRouter(prefix="/questions", tags=["questions"])

# role -> list of questions
QUESTIONS: dict[str, list[dict]] = {
    "SWE": [
        {
            "id": 1,
            "text": "Tell me about a challenging bug you fixed.",
            "key_points": [
                "root cause analysis",
                "debugging steps",
                "tools used",
                "impact",
                "lesson learned",
            ],
        },
        {
            "id": 2,
            "text": "Describe a system you designed.",
            "key_points": [
                "requirements",
                "trade-offs",
                "scalability",
                "bottlenecks",
                "monitoring",
            ],
        },
    ],
}


def _with_role(role: str, items: list[dict]) -> list[dict]:
    role = role.upper()
    return [
        {
            "id": q.get("id"),
            "role": role,
            "text": q.get("text"),
            "key_points": q.get("key_points", []),
        }
        for q in items
    ]


@router.get("/")
def get_all_questions():
    """Return all questions for all roles."""
    return {role: _with_role(role, items) for role, items in QUESTIONS.items()}


@router.get("/{role}")
def get_questions_by_role(role: str):
    """Return questions for a specific role."""
    items = QUESTIONS.get(role.upper(), [])
    return _with_role(role, items)
