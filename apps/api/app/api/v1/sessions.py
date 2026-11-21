from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.problem import Problem
from app.models.session import Session, TutorMessage
from app.schemas.sessions import (
    CodeRunRequest,
    CodeRunResponse,
    HeartbeatRequest,
    SessionCreateRequest,
    SessionResponse,
    StuckDeclarationRequest,
    TutorRequest,
    TutorResponse,
    UnlockStatusResponse,
)
from app.services.auth_service import AuthService
from app.services.code_runner import get_code_runner
from app.services.session_service import SessionService
from app.services.tutor_service import TutorService

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreateRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    user = await AuthService.get_current_user(request, db)
    session = await SessionService.create_session(
        db=db,
        student_id=user.id,
        problem_id=data.problem_id,
        assignment_id=data.assignment_id,
    )
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/heartbeat", response_model=SessionResponse)
async def post_heartbeat(
    session_id: str,
    data: HeartbeatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    session, _ = await SessionService.record_heartbeat(
        db=db,
        session_id=session_id,
        student_id=user.id,
        active_seconds=data.active_seconds,
        meaningful_edits=data.meaningful_edits,
        runs=data.runs,
        steps=data.steps,
        current_solution=data.current_solution,
        scratchpad=data.scratchpad,
    )
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/unlock-status", response_model=UnlockStatusResponse)
async def get_unlock_status(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    time_spent = int((datetime.utcnow() - session.attempt_started_at).total_seconds())
    can_unlock = (
        session.effort_score >= settings.EFFORT_E_MIN
        and time_spent >= settings.EFFORT_T_MIN_SECONDS
    )
    can_declare_stuck = time_spent >= settings.EFFORT_T_MIN_SECONDS

    return UnlockStatusResponse(
        session_id=session.id,
        state=session.state,
        effort_score=session.effort_score,
        effort_threshold=settings.EFFORT_E_MIN,
        time_spent_seconds=time_spent,
        time_min_seconds=settings.EFFORT_T_MIN_SECONDS,
        can_unlock=can_unlock,
        can_declare_stuck=can_declare_stuck,
        unlock_reason=session.unlock_reason,
    )


@router.post("/{session_id}/unlock", response_model=SessionResponse)
async def unlock_ai(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await AuthService.get_current_user(request, db)
    session = await SessionService.unlock_ai(db=db, session_id=session_id, student_id=user.id)
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/stuck", response_model=SessionResponse)
async def declare_stuck(
    session_id: str,
    data: StuckDeclarationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    session = await SessionService.declare_stuck(
        db=db, session_id=session_id, student_id=user.id, explanation=data.explanation
    )
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/run", response_model=CodeRunResponse)
async def run_code(
    session_id: str,
    data: CodeRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    problem = await db.get(Problem, session.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    runner = get_code_runner()
    test_cases = problem.test_cases if (data.run_test_cases and problem.test_cases) else None

    result = await runner.run(
        language=data.language,
        code=data.code,
        stdin=data.stdin,
        test_cases=test_cases,
        timeout_seconds=5.0,
    )

    # Save latest solution in session
    session.current_solution = data.code
    await db.commit()

    return CodeRunResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        test_results=result.test_results,
        timed_out=result.timed_out,
        error=result.error,
    )


@router.post("/{session_id}/tutor/message", response_model=TutorResponse)
async def tutor_message(
    session_id: str,
    data: TutorRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    msg = await TutorService.generate_tutor_reply(
        db=db,
        session_id=session_id,
        student_id=user.id,
        user_message=data.message,
        rung=data.rung,
    )
    return TutorResponse.model_validate(msg)


@router.get("/{session_id}/tutor/messages", response_model=List[TutorResponse])
async def list_tutor_messages(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(TutorMessage)
        .where(TutorMessage.session_id == session_id)
        .order_by(TutorMessage.ts.asc())
    )
    messages = result.scalars().all()
    return [TutorResponse.model_validate(m) for m in messages]


@router.post("/{session_id}/tutor/elaborate", response_model=TutorResponse)
async def tutor_elaborate(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.get_current_user(request, db)
    session = await db.get(Session, session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(TutorMessage)
        .where(TutorMessage.session_id == session_id, TutorMessage.role == "tutor")
        .order_by(TutorMessage.ts.desc())
    )
    last_tutor = result.scalars().first()
    if not last_tutor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No prior tutor response to elaborate on.",
        )

    msg = await TutorService.generate_tutor_reply(
        db=db,
        session_id=session_id,
        student_id=user.id,
        user_message="Could you please elaborate on your last explanation with more conceptual detail?",
        rung=last_tutor.rung or "help",
        is_elaborate=True,
    )
    return TutorResponse.model_validate(msg)
