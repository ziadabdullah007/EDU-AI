"""
EduCore AI Platform — School ORM Model

Represents a school tenant on the platform.
Each school owns its users, students, teachers, and all related data.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class School(Base, TimestampMixin, SoftDeleteMixin):
    """
    Represents a school registered on the EduCore platform.

    Each school is an isolated tenant. All business entities (students,
    teachers, classes, etc.) are scoped to a specific school.

    Table: schools
    """

    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique school identifier",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Official school name",
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="School physical address",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="School contact phone number",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="School contact email address",
    )
    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="School website URL",
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to the school logo image",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the school is currently active on the platform",
    )

    # ----------------------------- Relationships -----------------------------
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="school",
        lazy="select",
    )
    students: Mapped[list["Student"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="school",
        lazy="select",
    )
    teachers: Mapped[list["Teacher"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Teacher",
        back_populates="school",
        lazy="select",
    )
    classes: Mapped[list["Class"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Class",
        back_populates="school",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<School id={self.id} name='{self.name}'>"
