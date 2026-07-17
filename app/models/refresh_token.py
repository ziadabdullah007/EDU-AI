"""
EduCore AI Platform — Refresh Token ORM Model

Stores JWT refresh tokens for secure token rotation.
Each token is linked to a user and can be revoked independently.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """
    Persistent storage for JWT refresh tokens.

    Refresh tokens are stored server-side to enable:
    - Explicit logout (token revocation)
    - Detection of token reuse attacks
    - Token rotation on each refresh

    Business Rules:
    - Each token string must be unique.
    - Expired or revoked tokens cannot be used to refresh.
    - On logout, the token is marked is_revoked=True.

    Table: refresh_tokens
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique refresh token record identifier",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user this refresh token belongs to",
    )
    token: Mapped[str] = mapped_column(
        String(1000),
        unique=True,
        nullable=False,
        index=True,
        comment="The JWT refresh token string",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp when this token expires",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this token has been revoked (e.g., on logout)",
    )

    # ----------------------------- Relationships -----------------------------
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="refresh_tokens",
        lazy="select",
    )

    @property
    def is_valid(self) -> bool:
        """Return True if the token is not revoked and not expired."""
        from datetime import UTC
        return not self.is_revoked and self.expires_at > datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.is_revoked}>"
