"""
EduCore AI Platform — Student Repository

Handles all database operations for Student records.
No business logic. Only queries and persistence.
"""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Gender, Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    """Repository for Student database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Student, session)

    async def get_active_by_id(self, student_id: UUID, school_id: UUID) -> Student | None:
        """Return an active student scoped to a specific school."""
        stmt = select(Student).where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Student | None:
        """Find a student by their linked user account ID."""
        stmt = select(Student).where(
            and_(Student.user_id == user_id, Student.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def student_number_exists(
        self,
        student_number: str,
        school_id: UUID,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if a student number is already taken within a school.

        Args:
            student_number: The student number to check.
            school_id: The school to scope the check.
            exclude_id: Optional student ID to exclude (for updates).

        Returns:
            True if the number is already in use.
        """
        stmt = select(Student.id).where(
            and_(
                Student.student_number == student_number,
                Student.school_id == school_id,
                Student.deleted_at.is_(None),
            )
        )
        if exclude_id is not None:
            stmt = stmt.where(Student.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_students(
        self,
        school_id: UUID,
        search: str | None = None,
        is_active: bool | None = None,
        gender: Gender | None = None,
        class_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Student], int]:
        """
        List students within a school with search, filters, and pagination.

        Args:
            school_id: The school UUID for isolation.
            search: Optional text search on name or student number.
            is_active: Optional active status filter.
            gender: Optional gender filter.
            class_id: Optional filter to students enrolled in a specific class.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (students list, total count).
        """
        from app.models.enrollment import Enrollment, EnrollmentStatus

        stmt = select(Student).where(
            and_(Student.school_id == school_id, Student.deleted_at.is_(None))
        )

        if search:
            stmt = stmt.where(
                or_(
                    Student.first_name.ilike(f"%{search}%"),
                    Student.last_name.ilike(f"%{search}%"),
                    Student.student_number.ilike(f"%{search}%"),
                )
            )

        if is_active is not None:
            stmt = stmt.where(Student.is_active == is_active)

        if gender is not None:
            stmt = stmt.where(Student.gender == gender)

        if class_id is not None:
            stmt = stmt.join(
                Enrollment,
                and_(
                    Enrollment.student_id == Student.id,
                    Enrollment.class_id == class_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                ),
            )

        total = await self.count(stmt)

        order_col = getattr(Student, sort_by, Student.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        students = await self.execute_query(stmt)
        return students, total
