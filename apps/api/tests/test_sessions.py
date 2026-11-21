from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.problem import Problem
from app.models.session import Session
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_session_lifecycle_and_early_unlock_rejection(
    client: AsyncClient, sample_problem: Problem
):
    # Register and login student
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob Student",
            "email": "bob@student.com",
            "password": "password123",
            "role": "student",
        },
    )
    cookies = reg.cookies

    # 1. Start Session
    create_res = await client.post(
        "/api/v1/sessions", json={"problem_id": sample_problem.id}, cookies=cookies
    )
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["state"] == "attempt"
    assert session_data["effort_score"] == 0.0

    # 2. Check early unlock attempt is REJECTED
    unlock_res = await client.post(f"/api/v1/sessions/{session_id}/unlock", cookies=cookies)
    assert unlock_res.status_code == 400
    assert "Unlock threshold not met" in unlock_res.json()["detail"]

    # 3. Post Heartbeat with some effort
    hb_res = await client.post(
        f"/api/v1/sessions/{session_id}/heartbeat",
        json={
            "active_seconds": 120,
            "meaningful_edits": 80,
            "runs": 1,
            "steps": 2,
            "current_solution": "def two_sum(): pass",
        },
        cookies=cookies,
    )
    assert hb_res.status_code == 200
    assert hb_res.json()["effort_score"] > 0.0

    # 4. Check unlock status endpoint
    status_res = await client.get(f"/api/v1/sessions/{session_id}/unlock-status", cookies=cookies)
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["can_unlock"] is False

    # 5. Test Stuck declaration with too few words fails
    stuck_res = await client.post(
        f"/api/v1/sessions/{session_id}/stuck",
        json={"explanation": "I am stuck please help me."},
        cookies=cookies,
    )
    assert stuck_res.status_code in (400, 422)

    # 6. Test server-authoritative unlock when time & effort conditions are met
    # Simulate past time on session in DB
    async with TestSessionLocal() as db_session:
        s = await db_session.get(Session, session_id)
        assert s is not None
        s.attempt_started_at = datetime.utcnow() - timedelta(seconds=200)
        s.effort_score = 0.45
        await db_session.commit()

    # Now unlock should succeed
    valid_unlock = await client.post(f"/api/v1/sessions/{session_id}/unlock", cookies=cookies)
    assert valid_unlock.status_code == 200
    assert valid_unlock.json()["state"] == "guided"
    assert valid_unlock.json()["unlock_reason"] == "effort"
