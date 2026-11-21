import math
from datetime import datetime
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.problem import Problem
from app.models.session import Event, Session


class SessionService:
    # Default weights and expectation constants
    DEFAULT_WEIGHTS = {
        "a": 0.35,  # time weight
        "b": 0.25,  # meaningful edits weight
        "c": 0.15,  # test runs weight
        "d": 0.25,  # steps weight
    }

    @staticmethod
    def get_expectations(difficulty_b: float) -> Dict[str, float]:
        """Derive expected metrics based on IRT problem difficulty parameter."""
        factor = max(0.5, difficulty_b)
        return {
            "T_exp": 300.0 * factor,  # Expected active seconds (e.g. 5 min baseline)
            "M_exp": 180.0 * factor,  # Expected net typed chars
            "R_exp": max(2.0, 3.0 * factor),  # Expected test runs
            "S_exp": max(3.0, 4.0 * factor),  # Expected logical steps
        }

    @classmethod
    def calculate_effort_score(
        cls,
        active_seconds: float,
        meaningful_edits: int,
        runs: int,
        steps: int,
        difficulty_b: float = 1.0,
    ) -> float:
        """
        Calculates server-authoritative effort score E:
        E = 1 - exp(-(a*t/T_exp + b*m/M_exp + c*r/R_exp + d*s/S_exp))
        """
        exp = cls.get_expectations(difficulty_b)
        w = cls.DEFAULT_WEIGHTS

        exponent = (
            w["a"] * (active_seconds / exp["T_exp"])
            + w["b"] * (meaningful_edits / exp["M_exp"])
            + w["c"] * (runs / exp["R_exp"])
            + w["d"] * (steps / exp["S_exp"])
        )
        # Bounded between 0.0 and 1.0
        effort = 1.0 - math.exp(-exponent)
        return min(1.0, max(0.0, effort))

    @classmethod
    async def create_session(
        cls, db: AsyncSession, student_id: str, problem_id: str, assignment_id: Optional[str] = None
    ) -> Session:
        # Verify problem exists
        problem = await db.get(Problem, problem_id)
        if not problem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        session = Session(
            student_id=student_id,
            problem_id=problem_id,
            assignment_id=assignment_id,
            state="attempt",
            started_at=datetime.utcnow(),
            attempt_started_at=datetime.utcnow(),
            effort_score=0.0,
            help_cost=0.0,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def record_heartbeat(
        cls,
        db: AsyncSession,
        session_id: str,
        student_id: str,
        active_seconds: int,
        meaningful_edits: int,
        runs: int = 0,
        steps: int = 0,
        current_solution: Optional[str] = None,
        scratchpad: Optional[str] = None,
    ) -> Tuple[Session, float]:
        session = await db.get(Session, session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        problem = await db.get(Problem, session.problem_id)
        difficulty = problem.difficulty_b if problem else 1.0

        # Calculate time spent from attempt start
        total_time_spent = (datetime.utcnow() - session.attempt_started_at).total_seconds()
        effective_active_time = min(total_time_spent, active_seconds)

        # Update effort score
        score = cls.calculate_effort_score(
            active_seconds=effective_active_time,
            meaningful_edits=meaningful_edits,
            runs=runs,
            steps=steps,
            difficulty_b=difficulty,
        )
        session.effort_score = max(session.effort_score, score)

        if current_solution is not None:
            session.current_solution = current_solution
        if scratchpad is not None:
            session.scratchpad = scratchpad

        # Log aggregated heartbeat event
        event = Event(
            session_id=session.id,
            kind="heartbeat",
            payload={
                "active_seconds": active_seconds,
                "meaningful_edits": meaningful_edits,
                "runs": runs,
                "steps": steps,
                "effort_score": session.effort_score,
            },
        )
        db.add(event)
        await db.commit()
        await db.refresh(session)
        return session, session.effort_score

    @classmethod
    async def unlock_ai(cls, db: AsyncSession, session_id: str, student_id: str) -> Session:
        session = await db.get(Session, session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        if session.state != "attempt":
            return session

        time_spent = (datetime.utcnow() - session.attempt_started_at).total_seconds()

        # Enforce unlock rules: E >= E_min AND t >= t_min
        if (
            session.effort_score < settings.EFFORT_E_MIN
            or time_spent < settings.EFFORT_T_MIN_SECONDS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unlock threshold not met. Current effort: {session.effort_score:.2f}/{settings.EFFORT_E_MIN}, time: {int(time_spent)}s/{settings.EFFORT_T_MIN_SECONDS}s",
            )

        session.state = "guided"
        session.unlocked_at = datetime.utcnow()
        session.unlock_reason = "effort"
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def declare_stuck(
        cls, db: AsyncSession, session_id: str, student_id: str, explanation: str
    ) -> Session:
        session = await db.get(Session, session_id)
        if not session or session.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        if session.state != "attempt":
            return session

        time_spent = (datetime.utcnow() - session.attempt_started_at).total_seconds()
        if time_spent < settings.EFFORT_T_MIN_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can declare stuck only after {settings.EFFORT_T_MIN_SECONDS} seconds of genuine attempt.",
            )

        words = len(explanation.strip().split())
        if words < 35:  # ~40 words requirement
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please provide at least 35-40 words explaining what you tried and where you are blocked (current word count: {words}).",
            )

        session.state = "guided"
        session.unlocked_at = datetime.utcnow()
        session.unlock_reason = "stuck_declared"
        session.help_cost += 0.20  # Counts as slightly more reliance in scoring

        event = Event(
            session_id=session.id,
            kind="stuck_declared",
            payload={"explanation": explanation, "word_count": words},
        )
        db.add(event)
        await db.commit()
        await db.refresh(session)
        return session
