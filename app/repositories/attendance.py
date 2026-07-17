"""
EduCore AI Platform — Attendance Repository

Handles all database operations for Attendance records.
No business logic. Only queries and persistence.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Attendance, session)

    async def get_by_student_and_date(
        self, student_id: UUID, attendance_date: date
    ) -> Attendance | None:
        """
        Find an attendance record for a specific student on a specific date.

        Business Rule: One attendance record per student per day.

        Args:
            student_id: The student's UUID.
            attendance_date: The date to check.

        Returns:
            The Attendance record or None.
        """
        stmt = select(Attendance).where(
            and_(
                Attendance.student_id == student_id,
                Attendance.date == attendance_date,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_class_and_date(
        self,
        class_id: UUID,
        attendance_date: date,
    ) -> list[Attendance]:
        """
        Return all attendance records for a class on a specific date.

        Args:
            class_id: The class UUID.
            attendance_date: The date to report on.

        Returns:
            List of Attendance records.
        """
        stmt = select(Attendance).where(
            and_(
                Attendance.class_id == class_id,
                Attendance.date == attendance_date,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_student(
        self,
        student_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Attendance], int]:
        """
        Return paginated attendance history for a student.

        Args:
            student_id: The student's UUID.
            from_date: Optional start date filter.
            to_date: Optional end date filter.
            offset: Pagination offset.
            limit: Maximum records to return.

        Returns:
            Tuple of (attendance list, total count).
        """
        stmt = select(Attendance).where(Attendance.student_id == student_id)

        if from_date is not None:
            stmt = stmt.where(Attendance.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Attendance.date <= to_date)

        total = await self.count(stmt)
        stmt = stmt.order_by(Attendance.date.desc()).offset(offset).limit(limit)
        records = await self.execute_query(stmt)
        return records, total

    async def get_student_summary(
        self,
        student_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, int]:
        """
        Calculate attendance summary counts for a student.

        Args:
            student_id: The student's UUID.
            from_date: Optional start date.
            to_date: Optional end date.

        Returns:
            Dictionary mapping AttendanceStatus values to counts.
        """
        stmt = (
            select(Attendance.status, func.count(Attendance.id).label("cnt"))
            .where(Attendance.student_id == student_id)
            .group_by(Attendance.status)
        )

        if from_date is not None:
            stmt = stmt.where(Attendance.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Attendance.date <= to_date)

        result = await self.session.execute(stmt)
        rows = result.all()
        return {row.status.value: row.cnt for row in rows}

    async def list_by_class(
        self,
        class_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Attendance], int]:
        """
        Return paginated attendance records for an entire class.

        Args:
            class_id: The class UUID.
            from_date: Optional start date filter.
            to_date: Optional end date filter.
            offset: Pagination offset.
            limit: Maximum records to return.

        Returns:
            Tuple of (attendance list, total count).
        """
        stmt = select(Attendance).where(Attendance.class_id == class_id)

        if from_date is not None:
            stmt = stmt.where(Attendance.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Attendance.date <= to_date)

        total = await self.count(stmt)
        stmt = stmt.order_by(Attendance.date.desc()).offset(offset).limit(limit)
        records = await self.execute_query(stmt)
        return records, total
