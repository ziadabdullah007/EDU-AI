"""EduCore AI Platform — School Schemas"""

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class SchoolCreateRequest(BaseSchema):
    """Request to create a new school on the platform."""

    name: str = Field(min_length=2, max_length=255, description="Official school name")
    address: str | None = Field(default=None, max_length=1000, description="Physical address")
    phone: str | None = Field(default=None, max_length=20, description="Contact phone")
    email: EmailStr | None = Field(default=None, description="Contact email")
    website: str | None = Field(default=None, max_length=500, description="Website URL")
    logo_url: str | None = Field(default=None, max_length=1000, description="Logo image URL")


class SchoolUpdateRequest(BaseSchema):
    """Partial update for school details. All fields are optional."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, max_length=1000)
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=1000)


class SchoolResponse(UUIDSchema, TimestampSchema):
    """Public school profile response."""

    name: str
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    logo_url: str | None
    is_active: bool
