"""
EduCore AI Platform — Enrollment ORM Model

Tracks the relationship between Students and Classes.
Enrollment history is never deleted — only status changes are made.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import TimestampMixin


class EnrollmentStatus(str, enum.Enum):
    """
    Lifecycle states for a student enrollment.

    ACTIVE:      Student is currently enrolled in the class.
    TRANSFERRED: Student moved to another class (historical record kept).
    WITHDRAWN:   Student left the class voluntarily or was removed.
    """

    ACTIVE = "ACTIVE"
    TRANSFERRED = "TRANSFERRED"
    WITHDRAWN = "WITHDRAWN"


class Enrollment(Base, TimestampMixin):
    """
    Student-Class enrollment record.

    Tracks which students are assigned to which classes, including
    historical transfers and withdrawals.

    Business Rules:
    - A student can have at most ONE active enrollment at a time.
    - Transferring creates a new ACTIVE enrollment and sets the old to TRANSFERRED.
    - Enrollment records are NEVER hard-deleted.

    Table: enrollments
    """

    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique enrollment identifier",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The enrolled student",
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The class the student is enrolled in",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School context for fast scoped queries",
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status"),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        index=True,
        comment="Current enrollment status",
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp when student was enrolled",
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when enrollment was ended",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes about this enrollment (e.g., transfer reason)",
    )

    # ----------------------------- Relationships -----------------------------
    student: Mapped["Student"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="enrollments",
        lazy="select",
    )
    class_: Mapped["Class"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Class",
        back_populates="enrollments",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Enrollment id={self.id} student={self.student_id} "
            f"class={self.class_id} status='{self.status}'>"
        )
