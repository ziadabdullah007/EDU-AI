"""
EduCore AI Platform — Document ORM Model

Stores metadata for school documents. Actual file storage is external
(e.g., Supabase Storage, S3). Only metadata and references are kept here.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class DocumentCategory(str, enum.Enum):
    """
    Categories for organizing school documents.

    POLICY:     School rules and regulations.
    CURRICULUM: Academic plans and subject guides.
    FORM:       Administrative forms and templates.
    REPORT:     Reports and assessments.
    OTHER:      Uncategorized documents.
    """

    POLICY = "POLICY"
    CURRICULUM = "CURRICULUM"
    FORM = "FORM"
    REPORT = "REPORT"
    OTHER = "OTHER"


class Document(Base, TimestampMixin, SoftDeleteMixin):
    """
    Document metadata record.

    Only metadata is stored in this table. The actual file is stored
    externally (Supabase Storage or S3). The file_url field contains
    the reference to retrieve the file.

    Business Rules:
    - Only metadata is stored — no binary data in the database.
    - Deleted documents use soft-delete.

    Table: documents

    Future AI Integration Points:
    - Document contents feed a RAG (Retrieval Augmented Generation) pipeline.
    - Indexed documents enable AI-powered knowledge search.
    - Policy documents can be queried via an AI assistant.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique document identifier",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School this document belongs to",
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User who uploaded this document",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Document display title",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the document's contents",
    )
    file_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="External URL or path to the stored file",
    )
    file_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type of the file (e.g., 'application/pdf')",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes",
    )
    category: Mapped[DocumentCategory] = mapped_column(
        Enum(DocumentCategory, name="document_category"),
        nullable=False,
        default=DocumentCategory.OTHER,
        index=True,
        comment="Document category for organization and filtering",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this document is publicly visible",
    )

    # ----------------------------- Relationships -----------------------------
    school: Mapped["School"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "School",
        lazy="select",
    )
    uploader: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        lazy="select",
        foreign_keys=[uploaded_by],
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title='{self.title}' category='{self.category}'>"
