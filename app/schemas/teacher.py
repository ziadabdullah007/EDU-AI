"""EduCore AI Platform — Teacher Schemas"""

from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.utils.validators import validate_employee_number, validate_phone_number


class TeacherCreateRequest(BaseSchema):
    """Request to create a new teacher profile."""

    email: EmailStr = Field(description="Teacher's email (creates a User account)")
    password: str = Field(min_length=8, max_length=128, description="Initial password")
    employee_number: str = Field(description="School-assigned employee ID")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None)
    specialization: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)

    @field_validator("employee_number", mode="before")
    @classmethod
    def clean_employee_number(cls, v: str) -> str:
        return validate_employee_number(v)

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class TeacherUpdateRequest(BaseSchema):
    """Partial update for teacher profile."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None)
    specialization: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = Field(default=None)

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return validate_phone_number(v) if v else None


class TeacherResponse(UUIDSchema, TimestampSchema):
    """Teacher profile response."""

    school_id: UUID
    employee_number: str
    first_name: str
    last_name: str
    phone: str | None
    specialization: str | None
    bio: str | None
    is_active: bool
