"""
EduCore AI Platform — Base Pydantic Schemas

Shared base schemas and configuration used across all modules.
All schemas inherit from these bases for consistent behavior.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema with shared configuration.

    Attributes:
        model_config: Validates assignments, populates from ORM attributes,
                      and strips whitespace on string fields.
    """

    model_config = ConfigDict(
        from_attributes=True,   # Allow creating from SQLAlchemy ORM objects
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TimestampSchema(BaseSchema):
    """Adds read-only timestamp fields to a response schema."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Adds a UUID primary key field to a response schema."""

    id: UUID
