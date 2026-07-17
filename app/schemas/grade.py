"""
EduCore AI Platform — Grade Schemas

Request and response schemas for grade management.
Field names aligned to Grade ORM model (uses max_score not maximum_score).
"""

from uuid import UUID

from pydantic import Field, model_validator

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

    @model_validator(mode="after")
    def validate_score_le_max(self) -> "AddGradeRequest":
        """Validate that score does not exceed max_score at the schema level."""
        if self.score > self.max_score:
            raise ValueError(f"score ({self.score}) cannot exceed max_score ({self.max_score})")
        return self


class UpdateGradeRequest(BaseSchema):
    """Partial update for a grade record."""

    score: float | None = Field(default=None, ge=0)
    max_score: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=1000)
    term: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validate_score_le_max(self) -> "UpdateGradeRequest":
        """If both score and max_score provided, validate score <= max_score."""
        if self.score is not None and self.max_score is not None:
            if self.score > self.max_score:
                raise ValueError(f"score ({self.score}) cannot exceed max_score ({self.max_score})")
        return self


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
    """Aggregate grade statistics for a student."""

    student_id: UUID
    avg_score: float
    max_score: float
    min_score: float
    total_grades: int
