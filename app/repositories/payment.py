"""
EduCore AI Platform — Payment Repository

Handles all database operations for Payment records.
No business logic. Only queries and persistence.

Business Rule: Payments are NEVER hard-deleted. Records are immutable history.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus, PaymentType
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Payment, session)

    async def get_by_id_scoped(self, payment_id: UUID, school_id: UUID) -> Payment | None:
        """
        Return a payment record scoped to a specific school.

        Args:
            payment_id: The payment UUID.
            school_id: The school UUID for data isolation.

        Returns:
            The Payment or None.
        """
        stmt = select(Payment).where(
            and_(Payment.id == payment_id, Payment.school_id == school_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_student(
        self,
        student_id: UUID,
        status: PaymentStatus | None = None,
        payment_type: PaymentType | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Payment], int]:
        """
        List payments for a specific student with optional filters.

        Args:
            student_id: The student's UUID.
            status: Optional payment status filter.
            payment_type: Optional payment type filter.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (payments list, total count).
        """
        stmt = select(Payment).where(Payment.student_id == student_id)

        if status is not None:
            stmt = stmt.where(Payment.status == status)
        if payment_type is not None:
            stmt = stmt.where(Payment.payment_type == payment_type)

        total = await self.count(stmt)

        order_col = getattr(Payment, sort_by, Payment.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        return await self.execute_query(stmt), total

    async def list_by_school(
        self,
        school_id: UUID,
        search: str | None = None,
        status: PaymentStatus | None = None,
        payment_type: PaymentType | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Payment], int]:
        """
        List all payments across a school with optional filters.

        Search is performed on the `notes` field (the only text search target
        available on the Payment model).

        Args:
            school_id: The school UUID for isolation.
            search: Optional text search on payment notes.
            status: Optional payment status filter.
            payment_type: Optional payment type filter.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (payments list, total count).
        """
        stmt = select(Payment).where(Payment.school_id == school_id)

        if search:
            stmt = stmt.where(
                Payment.notes.ilike(f"%{search}%")  # type: ignore[union-attr]
            )
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        if payment_type is not None:
            stmt = stmt.where(Payment.payment_type == payment_type)

        total = await self.count(stmt)

        order_col = getattr(Payment, sort_by, Payment.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        return await self.execute_query(stmt), total

    async def get_student_balance_summary(self, student_id: UUID) -> dict[str, float]:
        """
        Compute the financial balance summary for a student.

        Aggregates total amounts by payment status: COMPLETED and PENDING.

        Args:
            student_id: The student's UUID.

        Returns:
            Dict containing total_charged, total_paid, total_pending.
        """
        # Total charged = all non-refunded payments
        charged_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(
                Payment.student_id == student_id,
                Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.PENDING]),
            )
        )
        paid_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(
                Payment.student_id == student_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        pending_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            and_(
                Payment.student_id == student_id,
                Payment.status == PaymentStatus.PENDING,
            )
        )

        charged_result = await self.session.execute(charged_stmt)
        paid_result = await self.session.execute(paid_stmt)
        pending_result = await self.session.execute(pending_stmt)

        return {
            "total_charged": float(charged_result.scalar_one()),
            "total_paid": float(paid_result.scalar_one()),
            "total_pending": float(pending_result.scalar_one()),
        }

    async def get_school_financial_summary(
        self, school_id: UUID
    ) -> dict[str, float | int]:
        """
        Compute aggregate financial stats for a school.

        Groups payments by status and aggregates amounts and counts.

        Args:
            school_id: The school UUID.

        Returns:
            Dict with total_revenue, total_pending, total_transactions.
        """
        stmt = select(
            Payment.status,
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
            func.count(Payment.id).label("count"),
        ).where(Payment.school_id == school_id).group_by(Payment.status)

        result = await self.session.execute(stmt)
        rows = result.all()

        summary: dict[str, float | int] = {
            "total_revenue": 0.0,
            "total_pending": 0.0,
            "total_transactions": 0,
        }
        for row in rows:
            summary["total_transactions"] = int(summary["total_transactions"]) + int(row.count)
            if row.status == PaymentStatus.COMPLETED:
                summary["total_revenue"] = float(row.total)
            elif row.status == PaymentStatus.PENDING:
                summary["total_pending"] = float(row.total)

        return summary
