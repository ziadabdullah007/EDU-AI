"""
EduCore AI Platform — Enrollment Repository

Handles all database operations for Enrollment records.
No business logic. Only queries and persistence.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    """Repository for Enrollment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Enrollment, session)

    async def get_active_enrollment(self, student_id: UUID) -> Enrollment | None:
        """
        Return the student's current active enrollment.

        Business Rule: A student may have at most one ACTIVE enrollment at a time.

        Args:
            student_id: The student's UUID.

        Returns:
            The active Enrollment or None.
        """
        stmt = select(Enrollment).where(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_id(
        self, enrollment_id: UUID, school_id: UUID
    ) -> Enrollment | None:
        """
        Return a specific enrollment scoped to a school.

        Args:
            enrollment_id: The enrollment UUID.
            school_id: The school UUID for isolation.

        Returns:
            The Enrollment or None.
        """
        stmt = (
            select(Enrollment)
            .join(Enrollment.student)
            .where(
                and_(
                    Enrollment.id == enrollment_id,
                    Enrollment.student.has(school_id=school_id),
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_student_and_class(
        self, student_id: UUID, class_id: UUID
    ) -> Enrollment | None:
        """
        Check if a student is already enrolled in a specific class (any status).

        Args:
            student_id: The student's UUID.
            class_id: The class UUID.

        Returns:
            The Enrollment if it exists (regardless of status), or None.
        """
        stmt = select(Enrollment).where(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.class_id == class_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_class(
        self,
        class_id: UUID,
        status: EnrollmentStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Enrollment], int]:
        """
        List enrollments for a specific class.

        Args:
            class_id: The class UUID.
            status: Optional status filter.
            offset: Pagination offset.
            limit: Maximum records to return.

        Returns:
            Tuple of (enrollments list, total count).
        """
        stmt = select(Enrollment).where(Enrollment.class_id == class_id)

        if status is not None:
            stmt = stmt.where(Enrollment.status == status)

        total = await self.count(stmt)
        stmt = stmt.offset(offset).limit(limit)
        enrollments = await self.execute_query(stmt)
        return enrollments, total

    async def list_by_student(
        self,
        student_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Enrollment], int]:
        """
        Return the full enrollment history for a student.

        Args:
            student_id: The student's UUID.
            offset: Pagination offset.
            limit: Maximum records to return.

        Returns:
            Tuple of (enrollments list, total count).
        """
        stmt = (
            select(Enrollment)
            .where(Enrollment.student_id == student_id)
            .order_by(Enrollment.enrolled_at.desc())
        )
        total = await self.count(stmt)
        stmt = stmt.offset(offset).limit(limit)
        enrollments = await self.execute_query(stmt)
        return enrollments, total
