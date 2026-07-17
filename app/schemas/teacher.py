"""
EduCore AI Platform — Teacher Schemas

Request and response schemas for teacher management endpoints.
Aligned to the Teacher ORM model columns exactly.
"""

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.utils.validators import validate_employee_number, validate_phone_number


class TeacherCreateRequest(BaseSchema):
    """
    Request to create a new teacher profile.

    The teacher must be linked to an existing User account (user_id).
    employee_number must be unique within the school.
    """

    user_id: UUID = Field(description="Existing User account ID to link to this teacher")
    employee_number: str = Field(description="School-assigned employee ID (unique per school)")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    specialization: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None)
    bio: str | None = Field(default=None)

    @field_validator("employee_number", mode="before")
    @classmethod
    def clean_employee_number(cls, v: str) -> str:
        """Normalize the employee number format."""
        return validate_employee_number(v)

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class TeacherUpdateRequest(BaseSchema):
    """Partial update for teacher profile. All fields are optional."""

    employee_number: str | None = Field(default=None)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    specialization: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("employee_number", mode="before")
    @classmethod
    def clean_employee_number(cls, v: str | None) -> str | None:
        return validate_employee_number(v) if v else None

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class TeacherResponse(UUIDSchema, TimestampSchema):
    """Teacher profile response. Never includes password data."""

    school_id: UUID
    user_id: UUID
    employee_number: str
    first_name: str
    last_name: str
    specialization: str | None
    phone: str | None
    bio: str | None
    is_active: bool
