"""
EduCore AI Platform — Payment Service

Business Rules:
- Amount must be positive (enforced by schema + DB constraint).
- Payment history is never deleted — only status changes.
- Balance summary reflects COMPLETED and PENDING payments.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import ForbiddenException, NotFoundException
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.models.user import User, UserRole
from app.repositories.payment import PaymentRepository
from app.repositories.student import StudentRepository
from app.schemas.payment import (
    CreatePaymentRequest,
    PaymentResponse,
    StudentBalanceSummary,
    UpdatePaymentRequest,
)
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class PaymentService:
    """Service for financial payment management."""

    def __init__(
        self,
        payment_repo: PaymentRepository,
        student_repo: StudentRepository,
    ) -> None:
        self._payment_repo = payment_repo
        self._student_repo = student_repo

    def _assert_school_access(self, school_id: UUID, requesting_user: User) -> None:
        """Raise ForbiddenException if user cannot access the given school."""
        if requesting_user.role == UserRole.SUPER_ADMIN:
            return
        if requesting_user.school_id != school_id:
            raise ForbiddenException("Access denied to this school's payment data.")

    async def create_payment(
        self,
        school_id: UUID,
        payload: CreatePaymentRequest,
        requesting_user: User,
    ) -> PaymentResponse:
        """
        Create a payment record for a student.

        Business Rules:
        - Student must belong to the same school.
        - Amount is validated positive by schema (gt=0).
        """
        self._assert_school_access(school_id, requesting_user)

        student = await self._student_repo.get_active_by_id(payload.student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{payload.student_id}' not found.")

        payment = Payment(
            school_id=school_id,
            student_id=payload.student_id,
            amount=payload.amount,
            currency=payload.currency,
            payment_type=payload.payment_type,
            status=payload.status,
            due_date=payload.due_date,
            reference_number=payload.reference_number,
            notes=payload.notes,
        )
        created = await self._payment_repo.create(payment)
        logger.info(
            "payment_created",
            payment_id=str(created.id),
            student_id=str(payload.student_id),
            amount=str(payload.amount),
        )
        return PaymentResponse.model_validate(created)

    async def update_payment(
        self,
        school_id: UUID,
        payment_id: UUID,
        payload: UpdatePaymentRequest,
        requesting_user: User,
    ) -> PaymentResponse:
        """Update payment status or metadata. Amount cannot be changed."""
        self._assert_school_access(school_id, requesting_user)

        payment = await self._payment_repo.get_by_id_scoped(payment_id, school_id)
        if payment is None:
            raise NotFoundException(f"Payment '{payment_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)
        updated = await self._payment_repo.update(payment_id, updates)
        logger.info("payment_updated", payment_id=str(payment_id))
        return PaymentResponse.model_validate(updated)

    async def get_payment(
        self, school_id: UUID, payment_id: UUID, requesting_user: User
    ) -> PaymentResponse:
        """Return a payment by ID, scoped to the school."""
        self._assert_school_access(school_id, requesting_user)
        payment = await self._payment_repo.get_by_id_scoped(payment_id, school_id)
        if payment is None:
            raise NotFoundException(f"Payment '{payment_id}' not found.")
        return PaymentResponse.model_validate(payment)

    async def get_student_balance(
        self, school_id: UUID, student_id: UUID, requesting_user: User
    ) -> StudentBalanceSummary:
        """Return the financial balance summary for a student."""
        self._assert_school_access(school_id, requesting_user)

        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")

        summary = await self._payment_repo.get_student_balance_summary(student_id)
        return StudentBalanceSummary(student_id=student_id, **summary)

    async def list_student_payments(
        self,
        school_id: UUID,
        student_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        status: PaymentStatus | None = None,
        payment_type: PaymentType | None = None,
    ) -> PaginatedResponse[PaymentResponse]:
        """List payment history for a student."""
        self._assert_school_access(school_id, requesting_user)

        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")

        payments, total = await self._payment_repo.list_by_student(
            student_id=student_id,
            status=status,
            payment_type=payment_type,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [PaymentResponse.model_validate(p) for p in payments]
        return build_paginated_response(items, total, params)

    async def list_school_payments(
        self,
        school_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        search: str | None = None,
        status: PaymentStatus | None = None,
        payment_type: PaymentType | None = None,
    ) -> PaginatedResponse[PaymentResponse]:
        """List all payments for a school."""
        self._assert_school_access(school_id, requesting_user)

        payments, total = await self._payment_repo.list_by_school(
            school_id=school_id,
            search=search,
            status=status,
            payment_type=payment_type,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [PaymentResponse.model_validate(p) for p in payments]
        return build_paginated_response(items, total, params)
