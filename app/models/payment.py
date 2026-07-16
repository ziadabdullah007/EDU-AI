"""
EduCore AI Platform — Payment ORM Model

Records financial transactions for students.
Payment history is permanent — records are never deleted.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import TimestampMixin


class PaymentType(str, enum.Enum):
    """Categories of school payments."""

    TUITION = "TUITION"
    REGISTRATION = "REGISTRATION"
    ACTIVITY = "ACTIVITY"
    BOOKS = "BOOKS"
    OTHER = "OTHER"


class PaymentStatus(str, enum.Enum):
    """
    Lifecycle states for a payment record.

    PENDING:   Payment has been created but not yet collected.
    COMPLETED: Payment was successfully received.
    FAILED:    Payment attempt was unsuccessful.
    REFUNDED:  Payment was returned to the payer.
    """

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base, TimestampMixin):
    """
    Financial payment record for a student.

    Business Rules:
    - amount must be positive (>0).
    - Payment records are NEVER deleted — only status changes occur.
    - due_date may be None for one-time immediate payments.

    Table: payments

    Future AI Integration Points:
    - Payment history feeds late payment prediction models.
    - Aggregated data supports financial analytics dashboards.
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique payment identifier",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Student this payment belongs to",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="School context for scoped queries",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Payment amount (must be positive)",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EGP",
        comment="ISO 4217 currency code (e.g., EGP, USD)",
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, name="payment_type"),
        nullable=False,
        index=True,
        comment="Category of this payment",
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
        comment="Current payment status",
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Payment due date (UTC)",
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when payment was received",
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="External reference or receipt number",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional administrative notes",
    )

    # ----------------------------- Relationships -----------------------------
    student: Mapped["Student"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Student",
        back_populates="payments",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} student={self.student_id} "
            f"amount={self.amount} status='{self.status}'>"
        )
