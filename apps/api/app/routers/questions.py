from fastapi import APIRouter
from typing import Dict, List

router = APIRouter(prefix="/questions", tags=["questions"])

# role -> list of questions
QUESTIONS: Dict[str, List[dict]] = {
    "SWE": [
        {
            "id": 1,
            "text": "Tell me about a challenging bug you fixed.",
            "key_points": [
                "root cause analysis", "debugging steps", "tools used", "impact", "lesson learned"
            ]
        },
        {
            "id": 2,
            "text": "Describe a system you designed.",
            "key_points": [
                "requirements", "trade-offs", "scalability", "bottlenecks", "monitoring"
            ]
        },
    ]
}

@router.get("/")
def get_all_questions():
    """Return all questions for all roles."""
    return QUESTIONS

@router.get("/{role}")
def get_questions_by_role(role: str):
    """Return questions for a specific role."""
    return QUESTIONS.get(role.upper(), [])