"""EduCore AI Platform — Student Repository"""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
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

    async def get_by_student_number(
        self, student_number: str, school_id: UUID
    ) -> Student | None:
        """Find a student by their school-assigned number."""
        stmt = select(Student).where(
            and_(
                Student.student_number == student_number,
                Student.school_id == school_id,
                Student.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_students(
        self,
        school_id: UUID,
        search: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Student], int]:
        """
        List students within a school with search and pagination.

        Returns:
            Tuple of (students, total_count).
        """
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

        total = await self.count(stmt)

        order_col = getattr(Student, sort_by, Student.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        students = await self.execute_query(stmt)
        return students, total
