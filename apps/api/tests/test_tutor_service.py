import pytest
from httpx import AsyncClient

from app.models.problem import Problem
from app.models.session import Session
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_tutor_service_requires_guided_state(client: AsyncClient, sample_problem: Problem):
    # Register and start session
    reg = await client.post("/api/v1/auth/register", json={
        "name": "Alice Tutor",
        "email": "alice.tutor@example.com",
        "password": "password123",
        "role": "student"
    })
    cookies = reg.cookies

    create_res = await client.post(
        "/api/v1/sessions",
        json={"problem_id": sample_problem.id},
        cookies=cookies
    )
    session_id = create_res.json()["id"]

    # In "attempt" state, tutor request must be rejected with 400
    tutor_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "Can you give me a hint?", "rung": "guide"},
        cookies=cookies
    )
    assert tutor_res.status_code == 400
    assert "only accessible in 'guided' mode" in tutor_res.json()["detail"]


@pytest.mark.asyncio
async def test_tutor_service_guided_rungs_and_elaborate(client: AsyncClient, sample_problem: Problem):
    reg = await client.post("/api/v1/auth/register", json={
        "name": "Carol Guided",
        "email": "carol.guided@example.com",
        "password": "password123",
        "role": "student"
    })
    cookies = reg.cookies

    create_res = await client.post(
        "/api/v1/sessions",
        json={"problem_id": sample_problem.id},
        cookies=cookies
    )
    session_id = create_res.json()["id"]

    # Transition to "guided" state
    async with TestSessionLocal() as db_session:
        s = await db_session.get(Session, session_id)
        assert s is not None
        s.state = "guided"
        await db_session.commit()

    # 1. Test Guide rung
    guide_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "What is the best approach?", "rung": "guide"},
        cookies=cookies
    )
    assert guide_res.status_code == 200
    guide_data = guide_res.json()
    assert guide_data["role"] == "tutor"
    assert guide_data["rung"] == "guide"
    assert guide_data["leak_check"]["passed"] is True

    # 2. Test Hint rung
    hint_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "What invariant can I check?", "rung": "hint"},
        cookies=cookies
    )
    assert hint_res.status_code == 200
    assert hint_res.json()["rung"] == "hint"

    # 3. Test Help rung
    help_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "Can you show an example?", "rung": "help"},
        cookies=cookies
    )
    assert help_res.status_code == 200
    assert help_res.json()["rung"] == "help"

    # 4. Test Critical Hint rung
    crit_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "What is step 1?", "rung": "critical_hint"},
        cookies=cookies
    )
    assert crit_res.status_code == 200
    assert crit_res.json()["rung"] == "critical_hint"

    # 5. Test Elaborate endpoint
    elab_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/elaborate",
        cookies=cookies
    )
    assert elab_res.status_code == 200
    assert elab_res.json()["role"] == "tutor"

    # 6. Test list tutor messages
    list_res = await client.get(
        f"/api/v1/sessions/{session_id}/tutor/messages",
        cookies=cookies
    )
    assert list_res.status_code == 200
    msgs = list_res.json()
    assert len(msgs) >= 8  # student + tutor messages


@pytest.mark.asyncio
async def test_tutor_budget_exhaustion(client: AsyncClient, sample_problem: Problem):
    reg = await client.post("/api/v1/auth/register", json={
        "name": "Dave Budget",
        "email": "dave.budget@example.com",
        "password": "password123",
        "role": "student"
    })
    cookies = reg.cookies

    create_res = await client.post(
        "/api/v1/sessions",
        json={"problem_id": sample_problem.id},
        cookies=cookies
    )
    session_id = create_res.json()["id"]

    async with TestSessionLocal() as db_session:
        s = await db_session.get(Session, session_id)
        assert s is not None
        s.state = "guided"
        await db_session.commit()

    # Exhaust budget of 6 hints
    for i in range(6):
        res = await client.post(
            f"/api/v1/sessions/{session_id}/tutor/message",
            json={"message": f"Hint request {i+1}", "rung": "guide"},
            cookies=cookies
        )
        assert res.status_code == 200

    # 7th hint must fail with budget exhaustion (HTTP 400)
    overflow_res = await client.post(
        f"/api/v1/sessions/{session_id}/tutor/message",
        json={"message": "Give me another hint", "rung": "guide"},
        cookies=cookies
    )
    assert overflow_res.status_code == 400
    assert "Hint budget exhausted" in overflow_res.json()["detail"]
