"""EduCore AI Platform — Class Schemas"""

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


def _validate_academic_year(v: str) -> str:
    """Validate academic year format YYYY-YYYY."""
    import re
    if not re.match(r"^\d{4}-\d{4}$", v):
        raise ValueError("academic_year must be in YYYY-YYYY format (e.g., '2024-2025')")
    parts = v.split("-")
    if int(parts[1]) != int(parts[0]) + 1:
        raise ValueError("Second year must be exactly one year after the first")
    return v


class ClassCreateRequest(BaseSchema):
    """Request to create a new class."""

    name: str = Field(min_length=2, max_length=100, description="Class display name")
    grade_level: str = Field(min_length=1, max_length=50, description="Grade or year level")
    academic_year: str = Field(description="Academic year (e.g., '2024-2025')")
    capacity: int = Field(default=30, ge=1, le=200, description="Maximum student count")
    teacher_id: UUID | None = Field(default=None, description="Teacher to assign (optional)")

    @field_validator("academic_year")
    @classmethod
    def validate_year(cls, v: str) -> str:
        return _validate_academic_year(v)


class ClassUpdateRequest(BaseSchema):
    """Partial update for class details."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    grade_level: str | None = Field(default=None, min_length=1, max_length=50)
    capacity: int | None = Field(default=None, ge=1, le=200)
    teacher_id: UUID | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class ClassResponse(UUIDSchema, TimestampSchema):
    """Class details response."""

    school_id: UUID
    teacher_id: UUID | None
    name: str
    grade_level: str
    academic_year: str
    capacity: int
    is_active: bool


class ClassWithEnrollmentCountResponse(ClassResponse):
    """Class response with current enrollment count."""

    enrolled_count: int
    available_slots: int

class AssignTeacherRequest(BaseSchema):
    """Request to assign or unassign a teacher to a class."""

    teacher_id: UUID | None = Field(
        default=None,
        description="Teacher UUID to assign. Use null to unassign the current teacher.",
    )