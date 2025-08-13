from typing import Dict, List

# role -> list of questions
QUESTIONS: Dict[str, List[dict]] = {
    "SWE": [
        {
            "id": 1,
            "text": "Tell me about a challenging bug you fixed.",
            "key_points": ["root cause analysis","debugging steps","tools used","impact","lesson learned"]
        },
        {
            "id": 2,
            "text": "Describe a system you designed.",
            "key_points": ["requirements","trade-offs","scalability","bottlenecks","monitoring"]
        },
    ]
}