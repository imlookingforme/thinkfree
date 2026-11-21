from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestCaseSchema(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False


class ProblemResponse(BaseModel):
    id: str
    title: str
    statement_md: str
    subject: str
    difficulty_b: float
    type: str  # theory | numeric | coding
    concept_ids: List[str]
    visibility: str
    rubric: Optional[Dict[str, Any]] = None
    test_cases: Optional[List[TestCaseSchema]] = None

    model_config = {"from_attributes": True}


class ProblemCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    statement_md: str = Field(..., min_length=10)
    subject: str = Field(..., min_length=2, max_length=100)
    difficulty_b: float = Field(default=1.0)
    type: str = Field(..., pattern="^(theory|numeric|coding)$")
    reference_solution_md: str = Field(..., min_length=10)
    concept_ids: List[str] = Field(default_factory=list)
    rubric: Dict[str, Any] = Field(default_factory=dict)
    test_cases: Optional[List[TestCaseSchema]] = None
    visibility: str = Field(default="public", pattern="^(public|course|private)$")
