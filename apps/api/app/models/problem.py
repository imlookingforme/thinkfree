from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.session import Session

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement_md: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    difficulty_b: Mapped[float] = mapped_column(Float, default=1.0)  # IRT difficulty parameter
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # theory | numeric | coding
    reference_solution_md: Mapped[str] = mapped_column(Text, nullable=False)
    rubric: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    test_cases: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    concept_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    visibility: Mapped[str] = mapped_column(
        String(50), default="public"
    )  # public | course | private
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variants: Mapped[List["ProblemVariant"]] = relationship(
        "ProblemVariant", back_populates="problem"
    )
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="problem")


class ProblemVariant(Base):
    __tablename__ = "problem_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id"), nullable=False)
    statement_md: Mapped[str] = mapped_column(Text, nullable=False)
    reference_solution_md: Mapped[str] = mapped_column(Text, nullable=False)
    test_cases: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    generation_seed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    problem: Mapped["Problem"] = relationship("Problem", back_populates="variants")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), nullable=False)
    problem_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    ai_policy: Mapped[str] = mapped_column(String(50), default="locked")  # locked | guided | open
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validation_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
