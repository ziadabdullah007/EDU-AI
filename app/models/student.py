"""
EduCore AI Platform — Student ORM Model

Represents a student's profile. Every student has an associated User
record for authentication and belongs to exactly one School.
"""

import enum
import uuid

from sqlalchemy import Date, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Gender(str, enum.Enum):
    """Student gender options."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Student(Base, TimestampMixin, SoftDeleteMixin):
    """
    Student profile record.

    A Student is always linked to a User (for auth) and a School.
    Academic records (grades, attendance, enrollments) reference the
    student by student_id.

    Business Rules:
    - student_number must be unique within a school.
    - A student can only belong to one school.
    - Deletion uses soft-delete (deleted_at timestamp).

    Table: students
    """

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("school_id", "student_number", name="uq_students_school_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique student identifier",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
        comment="Auth user account for this student",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School this student belongs to",
    )
    student_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="School-assigned student identifier (unique per school)",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Student's first name",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Student's last name",
    )
    date_of_birth: Mapped[uuid.UUID | None] = mapped_column(
        Date,
        nullable=True,
        comment="Student's date of birth",
    )
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"),
        nullable=True,
        comment="Student's gender",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Student's personal phone number",
    )
    parent_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Parent/guardian phone number",
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Student's home address",
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
        comment="Whether this student is currently active",
    )

    # ----------------------------- Relationships -----------------------------
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="student_profile",
        lazy="select",
    )
    school: Mapped["School"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "School",
        back_populates="students",
        lazy="select",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Enrollment",
        back_populates="student",
        lazy="select",
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Attendance",
        back_populates="student",
        lazy="select",
    )
    grades: Mapped[list["Grade"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Grade",
        back_populates="student",
        lazy="select",
    )
    payments: Mapped[list["Payment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Payment",
        back_populates="student",
        lazy="select",
    )

    @property
    def full_name(self) -> str:
        """Return the student's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Student id={self.id} number='{self.student_number}'>"
