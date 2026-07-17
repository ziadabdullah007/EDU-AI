"""
EduCore AI Platform — Student Schemas

Request and response schemas for student management endpoints.
Aligned to the Student ORM model columns exactly.
"""

from datetime import date
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.student import Gender
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.utils.validators import validate_phone_number, validate_student_number


class StudentCreateRequest(BaseSchema):
    """
    Request to create a new student profile.

    The student must be linked to an existing User account (user_id).
    student_number must be unique within the school.
    """

    user_id: UUID = Field(description="Existing User account ID to link to this student")
    student_number: str = Field(description="School-assigned student ID (unique per school)")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = Field(default=None)
    gender: Gender | None = Field(default=None)
    phone: str | None = Field(default=None)
    parent_phone: str | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("student_number", mode="before")
    @classmethod
    def clean_student_number(cls, v: str) -> str:
        """Normalize the student number format."""
        return validate_student_number(v)

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None

    @field_validator("parent_phone", mode="before")
    @classmethod
    def clean_parent_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class StudentUpdateRequest(BaseSchema):
    """Partial update for student profile. All fields are optional."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    student_number: str | None = Field(default=None)
    date_of_birth: date | None = Field(default=None)
    gender: Gender | None = Field(default=None)
    phone: str | None = Field(default=None)
    parent_phone: str | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    is_active: bool | None = Field(default=None)

    @field_validator("student_number", mode="before")
    @classmethod
    def clean_student_number(cls, v: str | None) -> str | None:
        return validate_student_number(v) if v else None

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None

    @field_validator("parent_phone", mode="before")
    @classmethod
    def clean_parent_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class StudentResponse(UUIDSchema, TimestampSchema):
    """Student profile response. Never includes password data."""

    school_id: UUID
    user_id: UUID
    student_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: Gender | None
    phone: str | None
    parent_phone: str | None
    address: str | None
    is_active: bool
