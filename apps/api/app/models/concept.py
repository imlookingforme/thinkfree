from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("concepts.id"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    parent: Mapped[Optional["Concept"]] = relationship(
        "Concept", remote_side=[id], backref="children"
    )


class ConceptEdge(Base):
    __tablename__ = "concept_edges"

    src_concept_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("concepts.id"), primary_key=True
    )
    dst_concept_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("concepts.id"), primary_key=True
    )
    kind: Mapped[str] = mapped_column(String(50), default="prereq")  # prereq | related
