import pytest
from httpx import AsyncClient

from app.models.problem import Problem
from app.models.session import Session
from app.services.validation_service import ValidationService
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_grade_explanation_pure(sample_problem: Problem):
    good_explanation = (
        "I recognized that the brute force approach takes O(n^2) time by checking every pair. "
        "Instead, we use a hash map to achieve O(n) linear time. As we iterate through each number, "
        "we compute the difference `diff = target - num` and look it up in constant O(1) time. "
        "If it exists in our lookup table, we return the pair of indices [lookup[diff], i]. "
        "Otherwise, we store the current number in the dictionary."
    )
    result = await ValidationService.grade_explanation(
        problem=sample_problem,
        solution_text="def two_sum(): pass",
        explanation_text=good_explanation
    )
    assert result.coverage >= 0.5
    assert result.confidence >= 0.5
    assert result.confidence_band in ["Moderate", "High"]
    assert len(result.rubric_scores) >= 1
    assert result.passed is True


@pytest.mark.asyncio
async def test_grade_explanation_poor_fails(sample_problem: Problem):
    poor_explanation = "I just wrote the code and it worked."
    result = await ValidationService.grade_explanation(
        problem=sample_problem,
        solution_text="pass",
        explanation_text=poor_explanation
    )
    assert result.coverage <= 0.6
    assert result.confidence_band in ["Low", "Moderate"]


@pytest.mark.asyncio
async def test_generate_isomorphic_variant(sample_problem: Problem):
    variant = await ValidationService.generate_isomorphic_variant(sample_problem)
    assert variant.problem_id == sample_problem.id
    assert variant.statement_md is not None
    assert len(variant.statement_md) > 10


@pytest.mark.asyncio
async def test_validation_api_explain_flow(client: AsyncClient, sample_problem: Problem):
    # Register and start session
    reg = await client.post("/api/v1/auth/register", json={
        "name": "Eve Explainer",
        "email": "eve.explainer@example.com",
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

    # Transition to guided then validate
    async with TestSessionLocal() as db_session:
        s = await db_session.get(Session, session_id)
        assert s is not None
        s.state = "guided"
        s.current_solution = "def two_sum(): return [0, 1]"
        await db_session.commit()

    # Submit explanation
    val_res = await client.post(
        f"/api/v1/validations/{session_id}/explain",
        json={
            "explanation": "We use a hash map to look up the difference target - num in O(1) time, ensuring an overall O(n) time complexity without nested loops."
        },
        cookies=cookies
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert "confidence" in val_data
    assert "confidence_band" in val_data
    assert "rubric_scores" in val_data
    assert val_data["session_state"] in ["done", "validate"]

    # Test teach-back question
    tb_res = await client.post(
        f"/api/v1/validations/{session_id}/teach-back",
        json={"student_reply": "Because hash maps use a hash function to map keys to buckets in O(1) time.", "turn": 1},
        cookies=cookies
    )
    assert tb_res.status_code == 200
    assert "junior_question" in tb_res.json()
    assert tb_res.json()["completed"] is False
