"""
EduCore AI Platform — School Repository

Handles all database operations for School records.
No business logic. Only queries and persistence.
"""


from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    """Repository for School database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(School, session)

    async def get_by_name(self, name: str) -> School | None:
        """
        Find a school by its exact name (case-insensitive).

        Args:
            name: The school name to look up.

        Returns:
            The School or None.
        """
        stmt = select(School).where(
            and_(
                School.name.ilike(name),
                School.deleted_at.is_(None),
            )
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
        List all schools with optional filters and pagination.

        Args:
            search: Optional text search on school name.
            is_active: Optional filter for active/inactive schools.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column name to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (schools list, total count).
        """
        stmt = select(School).where(School.deleted_at.is_(None))

        if search:
            stmt = stmt.where(School.name.ilike(f"%{search}%"))

        if is_active is not None:
            stmt = stmt.where(School.is_active == is_active)

        total = await self.count(stmt)

        order_col = getattr(School, sort_by, School.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        schools = await self.execute_query(stmt)
        return schools, total
