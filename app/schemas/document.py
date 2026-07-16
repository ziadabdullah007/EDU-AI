"""EduCore AI Platform — Document Schemas"""

from uuid import UUID

from pydantic import Field

from app.models.document import DocumentCategory
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class DocumentCreateRequest(BaseSchema):
    """Request to register document metadata."""

    title: str = Field(min_length=2, max_length=500, description="Document title")
    description: str | None = Field(default=None, max_length=2000)
    file_url: str = Field(min_length=10, max_length=2000, description="External file URL")
    file_type: str | None = Field(default=None, max_length=100, description="MIME type")
    file_size: int | None = Field(default=None, ge=0, description="File size in bytes")
    category: DocumentCategory = Field(
        default=DocumentCategory.OTHER, description="Document category"
    )


class DocumentUpdateRequest(BaseSchema):
    """Partial update for document metadata."""

    title: str | None = Field(default=None, min_length=2, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    file_url: str | None = Field(default=None, min_length=10, max_length=2000)
    file_type: str | None = Field(default=None, max_length=100)
    category: DocumentCategory | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class DocumentResponse(UUIDSchema, TimestampSchema):
    """Document metadata response."""

    school_id: UUID
    uploaded_by: UUID
    title: str
    description: str | None
    file_url: str
    file_type: str | None
    file_size: int | None
    category: DocumentCategory
    is_active: bool
