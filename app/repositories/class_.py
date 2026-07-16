"""EduCore AI Platform — Class Repository"""

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.base import BaseRepository


class ClassRepository(BaseRepository[Class]):
    """Repository for Class database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Class, session)

    async def get_active_by_id(self, class_id: UUID, school_id: UUID) -> Class | None:
        """Return an active class scoped to a specific school."""
        stmt = select(Class).where(
            and_(
                Class.id == class_id,
                Class.school_id == school_id,
                Class.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_enrollment_count(self, class_id: UUID) -> int:
        """Return the current number of active enrollments in a class."""
        stmt = select(func.count(Enrollment.id)).where(
            and_(
                Enrollment.class_id == class_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_classes(
        self,
        school_id: UUID,
        search: str | None = None,
        teacher_id: UUID | None = None,
        academic_year: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Class], int]:
        """List classes within a school with filters and pagination."""
        stmt = select(Class).where(
            and_(Class.school_id == school_id, Class.deleted_at.is_(None))
        )

        if search:
            stmt = stmt.where(
                or_(
                    Class.name.ilike(f"%{search}%"),
                    Class.grade_level.ilike(f"%{search}%"),
                )
            )

        if teacher_id is not None:
            stmt = stmt.where(Class.teacher_id == teacher_id)

        if academic_year is not None:
            stmt = stmt.where(Class.academic_year == academic_year)

        if is_active is not None:
            stmt = stmt.where(Class.is_active == is_active)

        total = await self.count(stmt)

        order_col = getattr(Class, sort_by, Class.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        classes = await self.execute_query(stmt)
        return classes, total
