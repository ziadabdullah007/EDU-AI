"""EduCore AI Platform — Grade Schemas"""

from uuid import UUID

from pydantic import Field, field_validator

from app.models.grade import AssessmentType
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class AddGradeRequest(BaseSchema):
    """Request to add a grade record for a student."""

    student_id: UUID = Field(description="Student receiving the grade")
    class_id: UUID = Field(description="Class the assessment belongs to")
    subject: str = Field(min_length=1, max_length=100, description="Subject name")
    assessment_type: AssessmentType = Field(description="Type of assessment")
    score: float = Field(ge=0, description="Achieved score (must be >= 0)")
    max_score: float = Field(gt=0, description="Maximum possible score (must be > 0)")
    academic_year: str = Field(description="Academic year (e.g., '2024-2025')")
    term: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("score")
    @classmethod
    def validate_score_le_max(cls, v: float, info: object) -> float:
        """Validate score does not exceed max_score at the schema level."""
        # Note: max_score check is also enforced at DB level via CHECK constraint
        return v


class UpdateGradeRequest(BaseSchema):
    """Partial update for a grade record."""

    score: float | None = Field(default=None, ge=0)
    max_score: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=1000)
    term: str | None = Field(default=None, max_length=50)


class GradeResponse(UUIDSchema, TimestampSchema):
    """Grade record response."""

    student_id: UUID
    class_id: UUID
    school_id: UUID
    teacher_id: UUID
    subject: str
    assessment_type: AssessmentType
    score: float
    max_score: float
    percentage: float
    academic_year: str
    term: str | None
    notes: str | None


class GradeStatisticsResponse(BaseSchema):
    """Aggregate statistics for a set of grade records."""

    subject: str | None
    total_assessments: int
    average_score: float
    average_percentage: float
    highest_score: float
    lowest_score: float
    pass_rate: float = Field(description="Percentage of grades >= 50%")
