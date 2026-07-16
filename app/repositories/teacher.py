"""EduCore AI Platform — Teacher Repository"""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    """Repository for Teacher database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Teacher, session)

    async def get_active_by_id(self, teacher_id: UUID, school_id: UUID) -> Teacher | None:
        """Return an active teacher scoped to a specific school."""
        stmt = select(Teacher).where(
            and_(
                Teacher.id == teacher_id,
                Teacher.school_id == school_id,
                Teacher.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Teacher | None:
        """Find a teacher by their linked user account ID."""
        stmt = select(Teacher).where(
            and_(Teacher.user_id == user_id, Teacher.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_employee_number(
        self, employee_number: str, school_id: UUID
    ) -> Teacher | None:
        """Find a teacher by employee number within a school."""
        stmt = select(Teacher).where(
            and_(
                Teacher.employee_number == employee_number,
                Teacher.school_id == school_id,
                Teacher.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_teachers(
        self,
        school_id: UUID,
        search: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Teacher], int]:
        """List teachers within a school with search and pagination."""
        stmt = select(Teacher).where(
            and_(Teacher.school_id == school_id, Teacher.deleted_at.is_(None))
        )

        if search:
            stmt = stmt.where(
                or_(
                    Teacher.first_name.ilike(f"%{search}%"),
                    Teacher.last_name.ilike(f"%{search}%"),
                    Teacher.employee_number.ilike(f"%{search}%"),
                    Teacher.specialization.ilike(f"%{search}%"),
                )
            )

        if is_active is not None:
            stmt = stmt.where(Teacher.is_active == is_active)

        total = await self.count(stmt)

        order_col = getattr(Teacher, sort_by, Teacher.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        teachers = await self.execute_query(stmt)
        return teachers, total
