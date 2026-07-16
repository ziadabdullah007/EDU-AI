"""
EduCore AI Platform — Class ORM Model

Represents a school classroom. Classes have a defined capacity,
belong to one school, and are assigned to one teacher.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Class(Base, TimestampMixin, SoftDeleteMixin):
    """
    School classroom entity.

    A Class belongs to one School, can have one Teacher assigned,
    and has a defined student capacity that must not be exceeded.

    Business Rules:
    - Class capacity cannot be exceeded on enrollment.
    - Only active teachers can be assigned.
    - One teacher may manage multiple classes.
    - academic_year format: '2024-2025'

    Table: classes
    """

    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique class identifier",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School this class belongs to",
    )
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Assigned teacher (nullable if unassigned)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Class display name (e.g., 'Grade 5 - A')",
    )
    grade_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Grade or year level (e.g., 'Grade 5', 'Year 3')",
    )
    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Academic year in format YYYY-YYYY (e.g., '2024-2025')",
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Maximum number of students allowed in this class",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this class is currently active",
    )

    # ----------------------------- Relationships -----------------------------
    school: Mapped["School"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "School",
        back_populates="classes",
        lazy="select",
    )
    teacher: Mapped["Teacher | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Teacher",
        back_populates="classes",
        lazy="select",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Enrollment",
        back_populates="class_",
        lazy="select",
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Attendance",
        back_populates="class_",
        lazy="select",
    )
    grades: Mapped[list["Grade"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Grade",
        back_populates="class_",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Class id={self.id} name='{self.name}' year='{self.academic_year}'>"
