from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.problem import Problem
    from app.models.user import User

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("problems.id"), nullable=False, index=True
    )
    assignment_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assignments.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(
        String(50), default="attempt", index=True
    )  # attempt | guided | validate | done | abandoned
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attempt_started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validate_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    unlock_reason: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # effort | stuck_declared | policy
    effort_score: Mapped[float] = mapped_column(Float, default=0.0)
    help_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Working state snapshot
    current_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scratchpad: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["User"] = relationship("User", back_populates="sessions")
    problem: Mapped["Problem"] = relationship("Problem", back_populates="sessions")
    events: Mapped[List["Event"]] = relationship(
        "Event", back_populates="session", cascade="all, delete-orphan"
    )
    tutor_messages: Mapped[List["TutorMessage"]] = relationship(
        "TutorMessage", back_populates="session", cascade="all, delete-orphan"
    )
    validations: Mapped[List["Validation"]] = relationship(
        "Validation", back_populates="session", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # heartbeat, run, paste, blur, focus, hint_request
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    session: Mapped["Session"] = relationship("Session", back_populates="events")


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # student | tutor
    rung: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # guide | help | hint | critical_hint
    content: Mapped[str] = mapped_column(Text, nullable=False)
    leak_check: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship("Session", back_populates="tutor_messages")


class Validation(Base):
    __tablename__ = "validations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)  # explain | similar
    variant_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("problem_variants.id"), nullable=True
    )
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_uri: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rubric_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=1.0)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    contested: Mapped[bool] = mapped_column(Boolean, default=False)
    contest_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship("Session", back_populates="validations")
