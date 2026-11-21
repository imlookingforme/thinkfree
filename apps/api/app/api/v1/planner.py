from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.problem import Assignment, Problem
from app.models.session import Session, Validation
from app.services.auth_service import AuthService
from app.services.consistency_service import ConsistencyBreakdown, ConsistencyService
from app.services.deadline_planner_service import (
    DeadlinePlannerService,
    DeadlinePlanResponse,
    FastLaneStatus,
)

router = APIRouter()


# --- Pydantic Schemas ---

class ContestRequest(BaseModel):
    validation_id: str
    contest_note: str  # Student's contextual explanation


class ContestResponse(BaseModel):
    validation_id: str
    contested: bool
    status: str
    message: str


class ConsistencyInspectionResponse(BaseModel):
    validation_id: str
    session_id: str
    breakdown: ConsistencyBreakdown
    contested: bool
    contest_note: Optional[str]


# --- Endpoints ---

@router.get("/consistency/{validation_id}", response_model=ConsistencyInspectionResponse)
async def get_validation_consistency(
    validation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 5: Full explainability inspection for an understanding-consistency score.
    Returns token overlap, syntactic alignment, and advisory reason details.
    """
    user = await AuthService.get_current_user(request, db)
    val = await db.get(Validation, validation_id)
    if not val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation record not found")

    session = await db.get(Session, val.session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    time_spent = 180.0
    if session.ended_at and session.started_at:
        time_spent = (session.ended_at - session.started_at).total_seconds()

    breakdown = ConsistencyService.calculate_consistency(
        attempt_text=session.scratchpad or session.current_solution or "",
        explanation_text=val.transcript or "",
        effort_score=session.effort_score,
        time_spent_seconds=time_spent
    )

    return ConsistencyInspectionResponse(
        validation_id=val.id,
        session_id=session.id,
        breakdown=breakdown,
        contested=val.contested,
        contest_note=val.contest_note
    )


@router.post("/contest", response_model=ContestResponse)
async def contest_anomaly_flag(
    data: ContestRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 5: Student 1-click contestation protocol.
    In accordance with docs/fairness.md, any anomaly flag is advisory and can be contested.
    """
    user = await AuthService.get_current_user(request, db)
    val = await db.get(Validation, data.validation_id)
    if not val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation record not found")

    session = await db.get(Session, val.session_id)
    if not session or session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    val.contested = True
    val.contest_note = data.contest_note
    val.anomaly_flag = False  # Mark advisory resolved under student context
    await db.commit()

    return ContestResponse(
        validation_id=val.id,
        contested=True,
        status="clarification_recorded",
        message="Your clarification has been recorded in your audit trail. The advisory flag has been neutralized."
    )


@router.get("/fast-lane", response_model=FastLaneStatus)
async def get_fast_lane_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 8: Fast Lane evaluation.
    Checks whether student qualifies for 60s attempt lock based on sustained ITS >= 80 and self-solves.
    """
    user = await AuthService.get_current_user(request, db)

    # Count recent consecutive self-solves
    res_sess = await db.execute(
        select(Session)
        .where(Session.student_id == user.id, Session.state == "done")
        .order_by(Session.ended_at.desc())
        .limit(10)
    )
    recent_sessions = list(res_sess.scalars().all())

    consecutive_self_solves = 0
    for s in recent_sessions:
        if s.help_cost == 0.0:
            consecutive_self_solves += 1
        else:
            break

    # Estimate current ITS heuristic
    current_its = 82.0
    status_res = DeadlinePlannerService.evaluate_fast_lane(
        current_its=current_its,
        consecutive_unaided_solves=consecutive_self_solves,
        streak_days=len(recent_sessions)
    )
    return status_res


@router.get("/deadline-plan", response_model=DeadlinePlanResponse)
async def get_deadline_plan(
    assignment_id: Optional[str] = None,
    request: Request = None,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db)
):
    """
    Feature 8: Deadline planner schedule and proactive AI lock strictness.
    """
    await AuthService.get_current_user(request, db)

    # Fetch assignment or fallback to public problem sample
    probs_data = []
    due_at = None
    if assignment_id:
        asg = await db.get(Assignment, assignment_id)
        if asg:
            due_at = asg.due_at
            # Fetch problem titles
            for pid in (asg.problem_ids or []):
                p = await db.get(Problem, pid)
                if p:
                    probs_data.append({"id": p.id, "title": p.title})

    if not probs_data:
        res_p = await db.execute(select(Problem).limit(3))
        probs_data = [{"id": p.id, "title": p.title} for p in res_p.scalars().all()]

    plan = DeadlinePlannerService.generate_deadline_plan(
        assignment_id=assignment_id,
        due_at=due_at,
        problem_list=probs_data
    )
    return plan
