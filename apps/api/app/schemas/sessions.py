from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    problem_id: str
    assignment_id: Optional[str] = None


class HeartbeatRequest(BaseModel):
    active_seconds: int = Field(..., ge=0, le=300)
    meaningful_edits: int = Field(..., ge=0)
    runs: int = Field(default=0, ge=0)
    steps: int = Field(default=0, ge=0)
    current_solution: Optional[str] = None
    scratchpad: Optional[str] = None


class StuckDeclarationRequest(BaseModel):
    explanation: str = Field(
        ..., min_length=40, description="Min ~40 words on what was tried and where blocked"
    )


class SessionResponse(BaseModel):
    id: str
    student_id: str
    problem_id: str
    assignment_id: Optional[str]
    state: str  # attempt | guided | validate | done | abandoned
    started_at: datetime
    attempt_started_at: datetime
    unlocked_at: Optional[datetime]
    validate_started_at: Optional[datetime]
    ended_at: Optional[datetime]
    unlock_reason: Optional[str]
    effort_score: float
    help_cost: float
    current_solution: Optional[str]
    scratchpad: Optional[str]

    model_config = {"from_attributes": True}


class UnlockStatusResponse(BaseModel):
    session_id: str
    state: str
    effort_score: float
    effort_threshold: float
    time_spent_seconds: int
    time_min_seconds: int
    can_unlock: bool
    can_declare_stuck: bool
    unlock_reason: Optional[str] = None


class CodeRunRequest(BaseModel):
    language: str = Field(default="python", pattern="^(python|javascript|c|cpp|java)$")
    code: str = Field(..., min_length=1)
    stdin: str = Field(default="")
    run_test_cases: bool = Field(default=True)


class CodeRunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    test_results: Optional[List[Dict[str, Any]]] = None
    timed_out: bool = False
    error: Optional[str] = None


class TutorRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    rung: str = Field(default="guide", pattern="^(guide|hint|help|critical_hint)$")


class TutorResponse(BaseModel):
    id: str
    session_id: str
    role: str
    rung: Optional[str]
    content: str
    leak_check: Optional[Dict[str, Any]]
    ts: datetime

    model_config = {"from_attributes": True}
