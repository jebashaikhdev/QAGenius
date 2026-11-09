from typing import TypedDict

class QAState(TypedDict):
    requirement: str
    analysis: str
    test_cases: str
    review: str
    iteration: int
    status: str