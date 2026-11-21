from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.analytics import update_student_mastery_and_stats
from app.database import get_db
from app.models.problem import Problem
from app.models.session import Session, Validation
from app.schemas.validations import (
    ExplainValidationRequest,
    ExplainValidationResponse,
    RubricItemResult,
    SimilarSubmitRequest,
    SimilarVariantResponse,
    TeachBackRequest,
    TeachBackResponse,
)
from app.services.auth_service import AuthService
from app.services.code_runner import get_code_runner
from app.services.validation_service import ValidationService

router = APIRouter()


@router.post("/{session_id}/explain", response_model=ExplainValidationResponse)
async def validate_by_explanation(
    session_id: str,
    data: ExplainValidationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    problem = await db.get(Problem, session.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Set validation start timestamp if first time
    if not session.validate_started_at:
        session.validate_started_at = datetime.utcnow()
    session.state = "validate"

    # Grade explanation against problem rubric
    result = await ValidationService.grade_explanation(
        problem=problem,
        solution_text=session.current_solution or "",
        explanation_text=data.explanation
    )

    # If passed, complete the session
    if result.passed:
        session.state = "done"
        session.ended_at = datetime.utcnow()

    # Save validation audit record
    val_record = Validation(
        session_id=session.id,
        mode="explain",
        transcript=data.explanation,
        rubric_scores=[r.model_dump() for r in result.rubric_scores],
        confidence=result.confidence,
        passed=result.passed,
        consistency_score=result.consistency_score,
        created_at=datetime.utcnow()
    )
    db.add(val_record)
    await db.commit()
    await db.refresh(session)

    # Trigger analytics & mastery update
    await update_student_mastery_and_stats(
        db=db,
        student_id=user.id,
        problem=problem,
        session=session,
        validation_passed=result.passed,
        validation_coverage=result.coverage
    )

    return ExplainValidationResponse(
        session_id=session.id,
        passed=result.passed,
        coverage=result.coverage,
        confidence=result.confidence,
        confidence_band=result.confidence_band,
        specificity=result.specificity,
        fluency=result.fluency,
        hesitation=result.hesitation,
        rubric_scores=[
            RubricItemResult(
                item=r.item,
                score=r.score,
                evidence_span=r.evidence_span,
                feedback=r.feedback
            ) for r in result.rubric_scores
        ],
        feedback_summary=result.feedback_summary,
        session_state=session.state
    )


@router.post("/{session_id}/teach-back", response_model=TeachBackResponse)
async def teach_back_question(
    session_id: str,
    data: TeachBackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    problem = await db.get(Problem, session.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    if data.turn >= 3:
        return TeachBackResponse(
            junior_question="That makes complete sense now! Thank you for walking me through each step so clearly.",
            turn=data.turn,
            completed=True
        )

    question = await ValidationService.get_teach_back_question(
        problem=problem,
        student_explanation=data.student_reply,
        conversation_turns=data.turn
    )

    return TeachBackResponse(
        junior_question=question,
        turn=data.turn,
        completed=False
    )


@router.post("/{session_id}/similar", response_model=SimilarVariantResponse)
async def get_or_create_similar_variant(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    problem = await db.get(Problem, session.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Generate isomorphic variant with verified solution
    variant = await ValidationService.generate_isomorphic_variant(problem)
    db.add(variant)
    await db.commit()
    await db.refresh(variant)

    session.state = "validate"
    await db.commit()

    return SimilarVariantResponse(
        variant_id=variant.id,
        problem_id=problem.id,
        statement_md=variant.statement_md,
        test_cases=variant.test_cases
    )


@router.post("/{session_id}/similar/submit")
async def submit_similar_variant_solution(
    session_id: str,
    data: SimilarSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    problem = await db.get(Problem, session.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    # Run solution against problem test cases in sandbox
    runner = get_code_runner()
    exec_res = await runner.run(
        language=data.language,
        code=data.solution,
        test_cases=problem.test_cases,
        timeout_seconds=5.0
    )

    passed = exec_res.exit_code == 0
    if passed:
        session.state = "done"
        session.ended_at = datetime.utcnow()

    val_record = Validation(
        session_id=session.id,
        mode="similar",
        transcript=data.solution,
        rubric_scores={"test_pass": 1.0 if passed else 0.0},
        confidence=1.0 if passed else 0.2,
        passed=passed,
        created_at=datetime.utcnow()
    )
    db.add(val_record)
    await db.commit()

    # Trigger analytics & mastery update
    await update_student_mastery_and_stats(
        db=db,
        student_id=user.id,
        problem=problem,
        session=session,
        validation_passed=passed,
        validation_coverage=1.0 if passed else 0.0
    )

    return {
        "passed": passed,
        "session_state": session.state,
        "stdout": exec_res.stdout,
        "test_results": exec_res.test_results
    }
