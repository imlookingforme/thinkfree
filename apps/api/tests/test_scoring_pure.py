import math

import pytest

from app.services.session_service import SessionService


def test_calculate_effort_score_zero_activity():
    """Effort score with zero activity should be exactly 0.0"""
    score = SessionService.calculate_effort_score(
        active_seconds=0, meaningful_edits=0, runs=0, steps=0, difficulty_b=1.0
    )
    assert score == pytest.approx(0.0, abs=1e-5)


def test_calculate_effort_score_moderate_activity():
    """
    Test effort score with specific values:
    active_seconds = 150 (half of T_exp=300) -> 0.35 * (150/300) = 0.175
    meaningful_edits = 90 (half of M_exp=180) -> 0.25 * (90/180) = 0.125
    runs = 0 -> 0.0
    steps = 2 (half of S_exp=4) -> 0.25 * (2/4) = 0.125
    Sum of exponents = 0.175 + 0.125 + 0.0 + 0.125 = 0.425
    Expected E = 1 - exp(-0.425) = 1 - 0.65377 = 0.3462
    """
    score = SessionService.calculate_effort_score(
        active_seconds=150, meaningful_edits=90, runs=0, steps=2, difficulty_b=1.0
    )
    expected = 1.0 - math.exp(-0.425)
    assert score == pytest.approx(expected, abs=1e-4)
    assert score < 0.35  # Just under minimum unlock threshold


def test_calculate_effort_score_exceeds_threshold():
    """High activity should yield effort score comfortably above 0.35"""
    score = SessionService.calculate_effort_score(
        active_seconds=240, meaningful_edits=150, runs=2, steps=3, difficulty_b=1.0
    )
    assert score > 0.45
    assert score <= 1.0
