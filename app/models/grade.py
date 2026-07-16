"""
EduCore AI Platform — Grade ORM Model

Records academic assessment scores for students.
Grades are immutable history — soft-deleted rather than hard-deleted.
"""

import enum
import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class AssessmentType(str, enum.Enum):
    """
    Types of academic assessments that can be graded.

    EXAM:       Major examination (midterm, final).
    QUIZ:       Short in-class assessment.
    ASSIGNMENT: Homework or project assignment.
    PROJECT:    Extended project work.
    """

    EXAM = "EXAM"
    QUIZ = "QUIZ"
    ASSIGNMENT = "ASSIGNMENT"
    PROJECT = "PROJECT"


class Grade(Base, TimestampMixin, SoftDeleteMixin):
    """
    Academic grade record for a student assessment.

    Business Rules:
    - score must be >= 0.
    - score must be <= max_score.
    - Only the teacher assigned to the class may create grades.
    - Deleted grades use soft-delete to preserve academic history.

    Table: grades

    Future AI Integration Points:
    - Grade sequences feed performance prediction models.
    - Aggregated grade stats can be used for academic risk scoring.
    """

    __tablename__ = "grades"
    __table_args__ = (
        CheckConstraint("score >= 0", name="ck_grades_score_non_negative"),
        CheckConstraint("max_score > 0", name="ck_grades_max_score_positive"),
        CheckConstraint("score <= max_score", name="ck_grades_score_le_max"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique grade record identifier",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Student this grade belongs to",
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Class the assessment was conducted in",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School context for scoped queries",
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Teacher who created this grade",
    )
    subject: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Subject the grade is for (e.g., 'Mathematics')",
    )
    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(AssessmentType, name="assessment_type"),
        nullable=False,
        index=True,
        comment="Type of assessment",
    )
    score: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Achieved score",
    )
    max_score: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="Maximum possible score for this assessment",
    )
    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Academic year in format YYYY-YYYY",
    )
    term: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Academic term (e.g., 'Term 1', 'First Semester')",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional teacher notes about this grade",
    )

    # ----------------------------- Relationships -----------------------------
    student: Mapped["Student"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="grades",
        lazy="select",
    )
    class_: Mapped["Class"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Class",
        back_populates="grades",
        lazy="select",
    )
    teacher: Mapped["Teacher"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Teacher",
        back_populates="grades",
        lazy="select",
    )

    @property
    def percentage(self) -> float:
        """Return the grade as a percentage."""
        if self.max_score == 0:
            return 0.0
        return round(float(self.score) / float(self.max_score) * 100, 2)

    def __repr__(self) -> str:
        return (
            f"<Grade id={self.id} student={self.student_id} "
            f"subject='{self.subject}' score={self.score}/{self.max_score}>"
        )
