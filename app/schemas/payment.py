"""EduCore AI Platform — Payment Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.payment import PaymentStatus, PaymentType
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class CreatePaymentRequest(BaseSchema):
    """Request to create a payment record for a student."""

    student_id: UUID = Field(description="Student this payment is for")
    amount: float = Field(gt=0, description="Payment amount (must be positive)")
    currency: str = Field(default="EGP", min_length=3, max_length=3, description="ISO 4217 code")
    payment_type: PaymentType = Field(description="Category of payment")
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Initial payment status"
    )
    due_date: datetime | None = Field(default=None, description="Payment due date (UTC)")
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


class UpdatePaymentRequest(BaseSchema):
    """Update a payment record's status or metadata."""

    status: PaymentStatus | None = Field(default=None)
    paid_at: datetime | None = Field(default=None, description="Actual payment timestamp")
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


class PaymentResponse(UUIDSchema, TimestampSchema):
    """Payment record response."""

    student_id: UUID
    school_id: UUID
    amount: float
    currency: str
    payment_type: PaymentType
    status: PaymentStatus
    due_date: datetime | None
    paid_at: datetime | None
    reference_number: str | None
    notes: str | None


class StudentBalanceResponse(BaseSchema):
    """Summarizes a student's financial standing."""

    student_id: UUID
    total_charged: float
    total_paid: float
    total_pending: float
    currency: str
