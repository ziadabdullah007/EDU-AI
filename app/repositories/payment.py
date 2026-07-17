"""
EduCore AI Platform — Payment Repository

Handles all database operations for Payment records.
No business logic. Only queries and persistence.

Business Rule: Payments are never deleted. Records are immutable history.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus, PaymentType
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Payment, session)

    async def get_by_id_scoped(self, payment_id: UUID, school_id: UUID) -> Payment | None:
        """
        Return a payment scoped to a specific school.

        Args:
            payment_id: The payment UUID.
            school_id: The school UUID for isolation.

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
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "payment_date",
        sort_order: str = "desc",
    ) -> tuple[list[Payment], int]:
        """
        List payments for a specific student with optional filters.

        Args:
            student_id: The student's UUID.
            status: Optional payment status filter.
            payment_type: Optional payment type filter.
            from_date: Optional start date filter.
            to_date: Optional end date filter.
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
        if from_date is not None:
            stmt = stmt.where(Payment.payment_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Payment.payment_date <= to_date)

        total = await self.count(stmt)

        order_col = getattr(Payment, sort_by, Payment.payment_date)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        payments = await self.execute_query(stmt)
        return payments, total

    async def list_by_school(
        self,
        school_id: UUID,
        search: str | None = None,
        status: PaymentStatus | None = None,
        payment_type: PaymentType | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "payment_date",
        sort_order: str = "desc",
    ) -> tuple[list[Payment], int]:
        """
        List all payments across a school with filters.

        Args:
            school_id: The school UUID for isolation.
            search: Optional text search on description.
            status: Optional payment status filter.
            payment_type: Optional payment type filter.
            from_date: Optional start date filter.
            to_date: Optional end date filter.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (payments list, total count).
        """
        stmt = select(Payment).where(Payment.school_id == school_id)

        if search:
            stmt = stmt.where(Payment.description.ilike(f"%{search}%"))
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        if payment_type is not None:
            stmt = stmt.where(Payment.payment_type == payment_type)
        if from_date is not None:
            stmt = stmt.where(Payment.payment_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Payment.payment_date <= to_date)

        total = await self.count(stmt)

        order_col = getattr(Payment, sort_by, Payment.payment_date)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        payments = await self.execute_query(stmt)
        return payments, total

    async def get_student_balance_summary(
        self,
        student_id: UUID,
    ) -> dict[str, float]:
        """
        Compute the total paid and total pending amounts for a student.

        Args:
            student_id: The student's UUID.

        Returns:
            Dict with total_paid and total_pending.
        """
        paid_stmt = select(func.sum(Payment.amount)).where(
            and_(
                Payment.student_id == student_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        pending_stmt = select(func.sum(Payment.amount)).where(
            and_(
                Payment.student_id == student_id,
                Payment.status == PaymentStatus.PENDING,
            )
        )

        paid_result = await self.session.execute(paid_stmt)
        pending_result = await self.session.execute(pending_stmt)

        return {
            "total_paid": float(paid_result.scalar_one_or_none() or 0),
            "total_pending": float(pending_result.scalar_one_or_none() or 0),
        }

    async def get_school_financial_summary(
        self,
        school_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, float | int]:
        """
        Compute aggregate financial stats for a school.

        Args:
            school_id: The school UUID.
            from_date: Optional start date.
            to_date: Optional end date.

        Returns:
            Dict with total_revenue, total_pending, total_transactions.
        """
        base_stmt = select(
            Payment.status,
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count"),
        ).where(Payment.school_id == school_id)

        if from_date is not None:
            base_stmt = base_stmt.where(Payment.payment_date >= from_date)
        if to_date is not None:
            base_stmt = base_stmt.where(Payment.payment_date <= to_date)

        base_stmt = base_stmt.group_by(Payment.status)
        result = await self.session.execute(base_stmt)
        rows = result.all()

        summary: dict[str, float | int] = {
            "total_revenue": 0.0,
            "total_pending": 0.0,
            "total_transactions": 0,
        }
        for row in rows:
            summary["total_transactions"] = int(summary["total_transactions"]) + int(row.count)
            if row.status == PaymentStatus.COMPLETED:
                summary["total_revenue"] = float(row.total or 0)
            elif row.status == PaymentStatus.PENDING:
                summary["total_pending"] = float(row.total or 0)

        return summary
