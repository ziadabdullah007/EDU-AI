"""
EduCore AI Platform — Attendance ORM Model

Records daily attendance for students within their classes.
One attendance record per student per day is enforced via a unique constraint.
"""

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import TimestampMixin


class AttendanceStatus(str, enum.Enum):
    """
    Valid attendance states for a student on a given day.

    PRESENT:  Student attended class.
    ABSENT:   Student was absent without documentation.
    LATE:     Student arrived after the session started.
    EXCUSED:  Student was absent with an accepted excuse.
    """

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class Attendance(Base, TimestampMixin):
    """
    Daily attendance record for a student in a class.

    Business Rules:
    - Only one record per student per day (enforced by unique constraint).
    - Only the teacher assigned to the class may record attendance.
    - Records are never deleted — only corrected via updates.

    Table: attendance

    Future AI Integration Points:
    - Attendance patterns feed into dropout prediction models.
    - Daily aggregates can be piped to an analytics pipeline.
    """

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "date", name="uq_attendance_student_date"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique attendance record identifier",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Student whose attendance is recorded",
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Class session the attendance is for",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School context for scoped queries",
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Teacher who recorded this attendance entry",
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date the attendance was taken (local school date)",
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendance_status"),
        nullable=False,
        index=True,
        comment="Attendance status for this student on this date",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes (e.g., reason for absence)",
    )

    # ----------------------------- Relationships -----------------------------
    student: Mapped["Student"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="attendance_records",
        lazy="select",
    )
    class_: Mapped["Class"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Class",
        back_populates="attendance_records",
        lazy="select",
    )
    recorded_by_teacher: Mapped["Teacher"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Teacher",
        back_populates="attendance_records",
        foreign_keys=[recorded_by],
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Attendance id={self.id} student={self.student_id} "
            f"date={self.date} status='{self.status}'>"
        )
