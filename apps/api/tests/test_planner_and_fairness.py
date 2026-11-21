from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.config import settings
from app.models.problem import Problem
from app.models.session import Session, Validation
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.consistency_service import ConsistencyService
from app.services.deadline_planner_service import DeadlinePlannerService
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_consistency_calculation_pure():
    """
    Verifies Feature 5: Consistency breakdown.
    - Strong alignment when explanation reuses attempt terminology.
    - Low score and advisory flag when attempt was empty/minimal but explanation is advanced.
    """
    # 1. High consistency case
    attempt = "def two_sum(nums, target): seen = {} for i, n in enumerate(nums): complement = target - n"
    expl_aligned = "In this two sum solution, we use a hash map seen to track complements target - n in linear time."
    res_high = ConsistencyService.calculate_consistency(
        attempt_text=attempt,
        explanation_text=expl_aligned,
        effort_score=0.8,
        time_spent_seconds=200
    )
    assert res_high.consistency_score >= 0.50
    assert not res_high.anomaly_flag

    # 2. Anomaly case (minimal attempt, complex explanation, fast time)
    attempt_empty = "pass"
    expl_complex = (
        "We implement an advanced Tarjan strongly connected components algorithm with low-link values, "
        "recursively inspecting depth first search trees and maintaining an auxiliary stack."
    )
    res_low = ConsistencyService.calculate_consistency(
        attempt_text=attempt_empty,
        explanation_text=expl_complex,
        effort_score=0.05,
        time_spent_seconds=30
    )
    assert res_low.consistency_score < 0.40
    assert res_low.anomaly_flag
    assert len(res_low.reasons) >= 1


@pytest.mark.asyncio
async def test_deadline_planner_and_fast_lane_pure():
    """
    Verifies Feature 8: Fast Lane eligibility and Deadline Planner urgency.
    """
    # Fast Lane check
    fl_eligible = DeadlinePlannerService.evaluate_fast_lane(
        current_its=85.0,
        consecutive_unaided_solves=4,
        streak_days=10
    )
    assert fl_eligible.is_eligible
    assert fl_eligible.reduced_lock_seconds == 60

    fl_ineligible = DeadlinePlannerService.evaluate_fast_lane(
        current_its=70.0,
        consecutive_unaided_solves=1,
        streak_days=3
    )
    assert not fl_ineligible.is_eligible
    assert fl_ineligible.reduced_lock_seconds == 180

    # Deadline schedule: Urgent window (< 24 hours)
    now = datetime(2026, 10, 27, 10, 0, 0)
    due_in_8h = now + timedelta(hours=8)
    plan_urgent = DeadlinePlannerService.generate_deadline_plan(
        assignment_id="asg_1",
        due_at=due_in_8h,
        problem_list=[{"id": "p1", "title": "P1"}, {"id": "p2", "title": "P2"}],
        now=now
    )
    assert plan_urgent.urgency_level == "critical"
    assert plan_urgent.ai_lock_strictness == "proactive_enforced"
    assert len(plan_urgent.schedule) == 2


@pytest.mark.asyncio
async def test_planner_and_fairness_api(client: AsyncClient):
    """
    Integration tests for:
    - GET /api/v1/planner/consistency/{validation_id}
    - POST /api/v1/planner/contest
    - GET /api/v1/planner/fast-lane
    - GET /api/v1/planner/deadline-plan
    """
    async with TestSessionLocal() as db:
        user = User(
            email="fairness_student@test.com",
            name="Fairness Student",
            password_hash="mock_hash",
            role="student"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        prob = Problem(
            title="Algorithm P1",
            statement_md="Sample problem",
            subject="Algorithms",
            difficulty_b=1.0,
            type="theory",
            reference_solution_md="ans",
            created_by=user.id
        )
        db.add(prob)
        await db.flush()

        sess = Session(
            student_id=user.id,
            problem_id=prob.id,
            state="done",
            started_at=datetime.now() - timedelta(minutes=10),
            ended_at=datetime.now(),
            scratchpad="def algo(): pass",
            effort_score=0.15,
            help_cost=0.0
        )
        db.add(sess)
        await db.flush()

        val = Validation(
            session_id=sess.id,
            mode="explain",
            transcript="Complicated explanation unrelated to scratchpad",
            confidence=0.85,
            passed=True,
            consistency_score=0.30,
            anomaly_flag=True,
            contested=False
        )
        db.add(val)
        await db.commit()
        await db.refresh(val)
        val_id = val.id
        user_id = user.id

    token = AuthService.create_access_token({"sub": user_id, "role": "student"})
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    # 1. Inspect consistency
    insp_res = await client.get(f"/api/v1/planner/consistency/{val_id}")
    assert insp_res.status_code == 200
    insp_data = insp_res.json()
    assert "breakdown" in insp_data
    assert "consistency_score" in insp_data["breakdown"]

    # 2. Contest advisory flag
    contest_res = await client.post(
        "/api/v1/planner/contest",
        json={"validation_id": val_id, "contest_note": "I practiced this algorithm yesterday on physical paper."}
    )
    assert contest_res.status_code == 200
    contest_data = contest_res.json()
    assert contest_data["contested"]
    assert contest_data["status"] == "clarification_recorded"

    # 3. Check Fast Lane Status
    fl_res = await client.get("/api/v1/planner/fast-lane")
    assert fl_res.status_code == 200
    assert "is_eligible" in fl_res.json()

    # 4. Check Deadline Plan
    plan_res = await client.get("/api/v1/planner/deadline-plan")
    assert plan_res.status_code == 200
    assert "urgency_level" in plan_res.json()
    assert len(plan_res.json()["schedule"]) >= 1
