"""
EduCore AI Platform — Teacher ORM Model

Represents a teacher's professional profile. A Teacher is linked to a
User (for auth), belongs to one School, and can teach multiple Classes.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Teacher(Base, TimestampMixin, SoftDeleteMixin):
    """
    Teacher professional profile.

    A Teacher can be assigned to multiple classes. Only active teachers
    can receive new class assignments.

    Business Rules:
    - employee_number must be unique within a school.
    - Inactive teachers cannot be assigned to new classes.
    - Soft-delete preserves historical assignment data.

    Table: teachers
    """

    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "employee_number", name="uq_teachers_school_employee"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique teacher identifier",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
        comment="Auth user account for this teacher",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School this teacher belongs to",
    )
    employee_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="School-assigned employee identifier (unique per school)",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Teacher's first name",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Teacher's last name",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Teacher's contact phone number",
    )
    specialization: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Teacher's subject or area of expertise",
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Short professional biography",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this teacher can be assigned to new classes",
    )

    # ----------------------------- Relationships -----------------------------
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="teacher_profile",
        lazy="select",
    )
    school: Mapped["School"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "School",
        back_populates="teachers",
        lazy="select",
    )
    classes: Mapped[list["Class"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Class",
        back_populates="teacher",
        lazy="select",
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Attendance",
        back_populates="recorded_by_teacher",
        foreign_keys="Attendance.recorded_by",
        lazy="select",
    )
    grades: Mapped[list["Grade"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Grade",
        back_populates="teacher",
        lazy="select",
    )

    @property
    def full_name(self) -> str:
        """Return the teacher's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Teacher id={self.id} employee='{self.employee_number}'>"
