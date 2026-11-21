from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.config import settings
from app.models.analytics import DailyStats, Mastery
from app.models.concept import Concept, ConceptEdge
from app.models.problem import Problem
from app.models.session import Session
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.scoring_service import ScoringService
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_bkt_mastery_dynamics():
    """
    Verifies Bayesian Knowledge Tracing updates:
    - Unaided success increases P(L) significantly
    - Heavy AI assistance attenuates P(L) increase
    - Failure decreases P(L)
    """
    initial_p = 0.30

    # 1. Unaided success (help_cost = 0)
    p_unaided = ScoringService.update_bkt(p_known=initial_p, is_correct=True, help_cost=0.0)
    assert p_unaided > initial_p
    assert p_unaided > 0.60, f"Expected strong jump on unaided solve, got {p_unaided}"

    # 2. Heavily aided success (help_cost = 1.2)
    p_aided = ScoringService.update_bkt(p_known=initial_p, is_correct=True, help_cost=1.2)
    assert p_aided > initial_p
    assert p_aided < p_unaided, "Aided success should yield strictly less mastery gain than unaided"

    # 3. Failure (is_correct = False)
    p_fail = ScoringService.update_bkt(p_known=initial_p, is_correct=False, help_cost=0.0)
    assert p_fail < initial_p, f"Failure should decrease mastery, got {p_fail} vs {initial_p}"


@pytest.mark.asyncio
async def test_sm2_spaced_repetition_intervals():
    """
    Verifies SM-2 algorithm:
    - Perfect recall (q=5) increases interval and Ease Factor
    - Failure (q<3) resets interval to 1 day
    """
    interval_0 = 1.0
    ease_0 = 2.5

    # First successful review (q=5)
    i1, ef1, next_rev1 = ScoringService.update_sm2(interval_days=interval_0, ease_factor=ease_0, quality_score=5)
    assert i1 == 1.0 or i1 == 6.0
    assert ef1 >= ease_0

    # Second review (q=5, interval=1.0)
    i2, ef2, _ = ScoringService.update_sm2(interval_days=2.0, ease_factor=ef1, quality_score=5)
    assert i2 == 6.0

    # Third review (q=5, interval=6.0)
    i3, ef3, _ = ScoringService.update_sm2(interval_days=6.0, ease_factor=ef2, quality_score=5)
    assert i3 > 6.0
    assert i3 == round(6.0 * ef3, 1)

    # Failure resets
    i_fail, ef_fail, _ = ScoringService.update_sm2(interval_days=i3, ease_factor=ef3, quality_score=2)
    assert i_fail == 1.0
    assert ef_fail < ef3


@pytest.mark.asyncio
async def test_its_and_adr_calculation():
    """
    Verifies pure formula calculation for Independent Thinking Score and AI Dependency Ratio.
    """
    # Pure unaided student
    its_perfect = ScoringService.calculate_its(
        unaided_success_rate=1.0,
        mean_validation_coverage=1.0,
        persistence_effort=1.0,
        spaced_retention=1.0
    )
    assert its_perfect == 100.0

    # Intermediate student
    its_mid = ScoringService.calculate_its(
        unaided_success_rate=0.70,
        mean_validation_coverage=0.80,
        persistence_effort=0.60,
        spaced_retention=0.75
    )
    expected = 100.0 * (0.30 * 0.70 + 0.30 * 0.80 + 0.20 * 0.60 + 0.20 * 0.75)
    assert its_mid == round(expected, 1)

    # ADR calculation
    rel_scores = [0.0, 0.0, 0.35 / 1.5, 0.55 / 1.5]
    adr = ScoringService.calculate_adr(rel_scores)
    assert 0.0 < adr < 0.5

    # EWMA Smoothing
    ewma = ScoringService.calculate_ewma_reliance(rel_scores, lambda_param=0.2)
    assert len(ewma) == 4
    assert ewma[0] == rel_scores[0]


@pytest.mark.asyncio
async def test_streak_calculation():
    """
    Verifies daily streak computation with freeze token support.
    """
    today = date.today()
    # Continuous 4 days
    dates = [today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=3)]
    assert ScoringService.calculate_streak(dates) == 4

    # 1-day gap with freeze token
    dates_gap = [today, today - timedelta(days=2)]
    assert ScoringService.calculate_streak(dates_gap, freeze_tokens_used=0) == 3
    assert ScoringService.calculate_streak(dates_gap, freeze_tokens_used=1) == 1


@pytest.mark.asyncio
async def test_analytics_api_endpoints(client: AsyncClient):
    """
    Integration test for /api/v1/analytics endpoints:
    - /dashboard
    - /mastery
    - /reviews
    - /explainability
    """
    # 1. Setup demo user, concept, problem, and completed session in DB
    async with TestSessionLocal() as db:
        user = User(
            email="analytics_student@test.com",
            name="Analytics Student",
            password_hash="mock_hash",
            role="student"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        concept_parent = Concept(id="math_basics", name="Math Basics", subject="Mathematics")
        concept_child = Concept(id="calculus_101", name="Calculus 101", parent_id="math_basics", subject="Mathematics")
        edge = ConceptEdge(src_concept_id="math_basics", dst_concept_id="calculus_101", kind="prereq")
        db.add_all([concept_parent, concept_child, edge])

        problem = Problem(
            title="Limits Problem",
            statement_md="Compute lim x->0 sin(x)/x",
            subject="Mathematics",
            difficulty_b=1.0,
            type="theory",
            reference_solution_md="1",
            rubric=[{"criterion": "L'Hopital rule or Taylor series", "max_score": 1.0}],
            concept_ids=["calculus_101"],
            created_by=user.id
        )
        db.add(problem)
        await db.flush()

        # Add DailyStats
        today = date.today()
        for i in range(5):
            ds = DailyStats(
                student_id=user.id,
                date=today - timedelta(days=i),
                active_minutes=45,
                flow_minutes=35,
                self_solves=3,
                ai_assisted=1,
                its=82.5,
                adr=0.25
            )
            db.add(ds)

        # Add a completed session
        sess = Session(
            student_id=user.id,
            problem_id=problem.id,
            state="done",
            started_at=datetime.now() - timedelta(minutes=20),
            ended_at=datetime.now(),
            help_cost=0.15,
            effort_score=0.85
        )
        db.add(sess)

        # Add Mastery record
        m1 = Mastery(
            student_id=user.id,
            concept_id="calculus_101",
            p_known=0.35,  # Struggling concept
            ease=2.5,
            interval_days=1.0,
            next_review_at=datetime.now() - timedelta(hours=2)  # Overdue
        )
        db.add(m1)
        await db.commit()
        user_id = user.id

    token = AuthService.create_access_token({"sub": user_id, "role": "student"})
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    # 2. Test /api/v1/analytics/dashboard
    dash_res = await client.get("/api/v1/analytics/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "its" in dash_data
    assert "adr" in dash_data
    assert "radar" in dash_data
    assert "explainability" in dash_data
    assert dash_data["current_streak"] >= 1
    assert "ITS" in dash_data["explainability"]

    # 3. Test /api/v1/analytics/mastery
    mastery_res = await client.get("/api/v1/analytics/mastery")
    assert mastery_res.status_code == 200
    mastery_data = mastery_res.json()
    assert len(mastery_data["concepts"]) >= 2
    # calculus_101 has p_known 0.35 so should be in weak_concepts
    assert any(c["concept_id"] == "calculus_101" for c in mastery_data["weak_concepts"])
    # math_basics has not been mastered, so calculus_101 should flag math_basics as unmet prerequisite!
    calc_item = next(c for c in mastery_data["concepts"] if c["concept_id"] == "calculus_101")
    assert "math_basics" in calc_item["prerequisites_unmet"]

    # 4. Test /api/v1/analytics/reviews
    reviews_res = await client.get("/api/v1/analytics/reviews")
    assert reviews_res.status_code == 200
    reviews_data = reviews_res.json()
    assert reviews_data["total_due"] >= 1
    assert any(r["concept_id"] == "calculus_101" for r in reviews_data["items"])

    # 5. Test /api/v1/analytics/explainability
    exp_res = await client.get("/api/v1/analytics/explainability")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "ITS" in exp_data["metrics"]
    assert "ADR" in exp_data["metrics"]
    assert "EWMA" in exp_data["metrics"]
