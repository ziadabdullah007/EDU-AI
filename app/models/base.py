"""
EduCore AI Platform — Base ORM Model Mixin

Provides shared columns (UUID PK, timestamps, soft delete) that all
business entity models inherit. This mixin keeps models DRY and ensures
every table in the platform has a consistent audit column structure.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds created_at and updated_at timestamp columns to a model.

    Timestamps are stored in UTC and managed automatically by
    SQLAlchemy server defaults.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="UTC timestamp when record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="UTC timestamp when record was last updated",
    )


class SoftDeleteMixin:
    """
    Adds deleted_at for soft-delete capability.

    Records with deleted_at IS NOT NULL are considered deleted.
    Queries should filter on this column to exclude deleted records.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
        comment="UTC timestamp when record was soft-deleted (NULL = active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Return True if the record has been soft-deleted."""
        return self.deleted_at is not None
