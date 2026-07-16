"""EduCore AI Platform — Student Schemas"""

from datetime import date
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.student import Gender
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.utils.validators import validate_phone_number, validate_student_number


class StudentCreateRequest(BaseSchema):
    """Request to create a new student profile."""

    email: EmailStr = Field(description="Student's email (creates a User account)")
    password: str = Field(min_length=8, max_length=128, description="Initial password")
    student_number: str = Field(description="School-assigned student ID")
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
    date_of_birth: date | None = Field(default=None)
    gender: Gender | None = Field(default=None)
    phone: str | None = Field(default=None)
    parent_phone: str | None = Field(default=None)
    address: str | None = Field(default=None, max_length=500)
    is_active: bool | None = Field(default=None)

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
    student_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: Gender | None
    phone: str | None
    parent_phone: str | None
    address: str | None
    is_active: bool
