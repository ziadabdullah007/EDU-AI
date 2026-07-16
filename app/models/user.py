"""
EduCore AI Platform — User ORM Model

Represents an authentication identity for every person on the platform.
A User is the authentication record; role-specific profiles (Student,
Teacher) are separate entities linked via user_id.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """
    Defines the access roles available on the platform.

    SUPER_ADMIN:  Platform-level admin. Can manage all schools.
    SCHOOL_ADMIN: Manages a single school's operations.
    TEACHER:      Can record attendance and grades for their classes.
    STUDENT:      Read-only access to their own academic records.
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    Authentication identity record for every platform user.

    Users are the authentication entity. Role-specific details are stored
    in related Student or Teacher profile records.

    Business Rules:
    - Email must be unique across the entire platform.
    - Passwords are always stored as bcrypt hashes.
    - Inactive users cannot authenticate.
    - SUPER_ADMIN has no school_id (platform-wide access).

    Table: users
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address — must be unique platform-wide",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hashed password — never store plain text",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's first name",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's last name",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        index=True,
        comment="User's platform role for RBAC",
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="School this user belongs to (NULL for SUPER_ADMIN)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this user can authenticate",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this user's email has been verified",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the user's last successful login",
    )

    # ----------------------------- Relationships -----------------------------
    school: Mapped["School | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "School",
        back_populates="users",
        lazy="select",
    )
    student_profile: Mapped["Student | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="user",
        uselist=False,
        lazy="select",
    )
    teacher_profile: Mapped["Teacher | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Teacher",
        back_populates="user",
        uselist=False,
        lazy="select",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "RefreshToken",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
