from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Mastery(Base):
    __tablename__ = "mastery"

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    concept_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("concepts.id"), primary_key=True
    )
    p_known: Mapped[float] = mapped_column(Float, default=0.3)  # Bayesian Knowledge Tracing prior
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    next_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ease: Mapped[float] = mapped_column(Float, default=2.5)  # SM-2 ease factor
    interval_days: Mapped[float] = mapped_column(Float, default=1.0)

    student: Mapped["User"] = relationship("User", back_populates="mastery_records")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    active_minutes: Mapped[int] = mapped_column(Integer, default=0)
    flow_minutes: Mapped[int] = mapped_column(Integer, default=0)
    self_solves: Mapped[int] = mapped_column(Integer, default=0)
    ai_assisted: Mapped[int] = mapped_column(Integer, default=0)
    its: Mapped[float] = mapped_column(Float, default=0.0)  # Independent Thinking Score
    adr: Mapped[float] = mapped_column(Float, default=0.0)  # AI Dependency Ratio


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(100), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    signature: Mapped[str] = mapped_column(String(255), nullable=False)
