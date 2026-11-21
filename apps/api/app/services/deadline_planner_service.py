from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FastLaneStatus(BaseModel):
    is_eligible: bool
    consecutive_high_its: int
    threshold_its: float
    streak_days: int
    benefit_description: str
    reduced_lock_seconds: int


class DeadlinePlanItem(BaseModel):
    problem_id: str
    problem_title: str
    estimated_minutes: int
    scheduled_date: str
    ai_policy: str
    lock_enforced: bool


class DeadlinePlanResponse(BaseModel):
    assignment_id: Optional[str]
    due_at: Optional[datetime]
    hours_remaining: float
    urgency_level: str  # "relaxed" | "moderate" | "urgent" | "critical"
    ai_lock_strictness: str  # "normal" | "proactive_enforced"
    warning_message: Optional[str]
    schedule: List[DeadlinePlanItem]


class DeadlinePlannerService:
    """
    Feature 8: Deadline planner & Fast Lane.
    Prevents last-minute AI panics before deadlines by scheduling spaced attempt blocks.
    Enforces proactive AI lock rules as deadlines approach, and rewards consistent performers
    with Fast Lane acceleration.
    """

    @staticmethod
    def evaluate_fast_lane(
        current_its: float,
        consecutive_unaided_solves: int,
        streak_days: int
    ) -> FastLaneStatus:
        """
        Fast Lane: If student maintains high ITS (>= 80) and has >= 3 consecutive
        unaided solves, initial attempt lock requirement is reduced from 180s to 60s.
        """
        is_eligible = current_its >= 80.0 and consecutive_unaided_solves >= 3
        reduced_lock = 60 if is_eligible else 180
        desc = (
            "Fast Lane Active: You have demonstrated sustained cognitive independence (ITS >= 80, 3+ self-solves). "
            "Attempt lock time is reduced to 60 seconds."
            if is_eligible
            else "Standard Track: Solve 3 problems unaided with ITS >= 80 to unlock the 60s Fast Lane."
        )

        return FastLaneStatus(
            is_eligible=is_eligible,
            consecutive_high_its=consecutive_unaided_solves,
            threshold_its=80.0,
            streak_days=streak_days,
            benefit_description=desc,
            reduced_lock_seconds=reduced_lock
        )

    @staticmethod
    def generate_deadline_plan(
        assignment_id: Optional[str],
        due_at: Optional[datetime],
        problem_list: List[Dict[str, Any]],
        now: Optional[datetime] = None
    ) -> DeadlinePlanResponse:
        """
        Generates a spaced preparation schedule and determines AI lock policies.
        When due_at is < 24 hours away, panic-pasting risks spike, so AI lock
        strictness is upgraded to 'proactive_enforced' (no stuck bypass without full 35-word justification).
        """
        current_time = now or datetime.now()
        if not due_at:
            # Default mock deadline: 48 hours from now
            due_at = current_time + timedelta(hours=48)

        diff = due_at - current_time
        hours_remaining = max(0.1, round(diff.total_seconds() / 3600.0, 1))

        if hours_remaining <= 12:
            urgency = "critical"
            strictness = "proactive_enforced"
            warning = "Critical deadline window (<12h). AI locks are strictly enforced to prevent panic copy-pasting."
        elif hours_remaining <= 24:
            urgency = "urgent"
            strictness = "proactive_enforced"
            warning = "Deadline approaching (<24h). Complete your attempts early to allow time for the validation phase."
        elif hours_remaining <= 72:
            urgency = "moderate"
            strictness = "normal"
            warning = None
        else:
            urgency = "relaxed"
            strictness = "normal"
            warning = None

        # Build schedule items spaced across available days
        num_problems = max(1, len(problem_list))
        schedule: List[DeadlinePlanItem] = []

        for idx, p in enumerate(problem_list):
            hours_offset = (idx + 1) * (hours_remaining / (num_problems + 1))
            item_date = (current_time + timedelta(hours=hours_offset)).strftime("%Y-%m-%d %H:%M")
            schedule.append(
                DeadlinePlanItem(
                    problem_id=p.get("id", f"p_{idx}"),
                    problem_title=p.get("title", f"Problem {idx+1}"),
                    estimated_minutes=25,
                    scheduled_date=item_date,
                    ai_policy="locked",
                    lock_enforced=True
                )
            )

        return DeadlinePlanResponse(
            assignment_id=assignment_id,
            due_at=due_at,
            hours_remaining=hours_remaining,
            urgency_level=urgency,
            ai_lock_strictness=strictness,
            warning_message=warning,
            schedule=schedule
        )
