"""EduCore AI Platform — School Repository"""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    """Repository for School database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(School, session)

    async def get_active_by_id(self, school_id: UUID) -> School | None:
        """Return an active school by its ID."""
        stmt = select(School).where(
            and_(School.id == school_id, School.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_schools(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[School], int]:
        """
        List schools with optional filtering, search, and pagination.

        Returns:
            Tuple of (schools, total_count).
        """
        stmt = select(School).where(School.deleted_at.is_(None))

        if search:
            stmt = stmt.where(
                or_(
                    School.name.ilike(f"%{search}%"),
                    School.email.ilike(f"%{search}%"),
                )
            )

        if is_active is not None:
            stmt = stmt.where(School.is_active == is_active)

        total = await self.count(stmt)

        order_col = getattr(School, sort_by, School.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        schools = await self.execute_query(stmt)
        return schools, total
