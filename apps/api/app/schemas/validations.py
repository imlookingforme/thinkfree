from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RubricItemResult(BaseModel):
    item: str
    score: float
    evidence_span: str
    feedback: str


class ExplainValidationRequest(BaseModel):
    explanation: str = Field(..., min_length=10, max_length=10000)
    audio_base64: Optional[str] = None


class ExplainValidationResponse(BaseModel):
    session_id: str
    passed: bool
    coverage: float
    confidence: float
    confidence_band: str
    specificity: float
    fluency: float
    hesitation: float
    rubric_scores: List[RubricItemResult]
    feedback_summary: str
    session_state: str


class TeachBackRequest(BaseModel):
    student_reply: str = Field(..., min_length=5)
    turn: int = Field(default=1, ge=1, le=5)


class TeachBackResponse(BaseModel):
    junior_question: str
    turn: int
    completed: bool


class SimilarVariantResponse(BaseModel):
    variant_id: str
    problem_id: str
    statement_md: str
    test_cases: Optional[List[Dict[str, Any]]] = None


class AudioTranscribeResponse(BaseModel):
    transcript: str
    engine: str
    language: str
    duration_seconds: float
    confidence: float
    fluency_telemetry: Dict[str, Any]


class AudioDefenseRequest(BaseModel):
    transcript: str = Field(..., min_length=5)
    language: str = "en"
    duration_seconds: float = 15.0
    audio_base64: Optional[str] = None


class SimilarSubmitRequest(BaseModel):
    solution: str = Field(..., min_length=2)
    language: str = Field(default="python")
