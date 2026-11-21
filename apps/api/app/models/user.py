from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.analytics import Mastery
    from app.models.session import Session

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lti_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    plan: Mapped[str] = mapped_column(String(50), default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship("User", back_populates="institution")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="institution")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default="student", index=True
    )  # student | professor | admin
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=True
    )
    locale: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    consent_flags: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {
            "audio_retention": True,
            "analytics_sharing": True,
            "professor_sharing": True,
        },
    )

    institution: Mapped[Optional["Institution"]] = relationship(
        "Institution", back_populates="users"
    )
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="student")
    mastery_records: Mapped[List["Mastery"]] = relationship("Mastery", back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    professor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    institution: Mapped[Optional["Institution"]] = relationship(
        "Institution", back_populates="courses"
    )
    professor: Mapped["User"] = relationship("User", foreign_keys=[professor_id])
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id"), primary_key=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    student: Mapped["User"] = relationship("User")
