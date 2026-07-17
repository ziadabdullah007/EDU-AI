"""
EduCore AI Platform — Grade Repository

Handles all database operations for Grade records.
No business logic. Only queries and persistence.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade import AssessmentType, Grade
from app.repositories.base import BaseRepository


class GradeRepository(BaseRepository[Grade]):
    """Repository for Grade database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Grade, session)

    async def get_active_by_id(self, grade_id: UUID, school_id: UUID) -> Grade | None:
        """
        Return an active (non-deleted) grade scoped to a school.

        Args:
            grade_id: The grade UUID.
            school_id: The school UUID for isolation.

        Returns:
            The Grade or None.
        """
        stmt = select(Grade).where(
            and_(
                Grade.id == grade_id,
                Grade.school_id == school_id,
                Grade.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_student(
        self,
        student_id: UUID,
        school_id: UUID,
        class_id: UUID | None = None,
        assessment_type: AssessmentType | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Grade], int]:
        """
        List all grades for a student with optional filters.

        Args:
            student_id: The student's UUID.
            school_id: The school UUID for isolation.
            class_id: Optional class filter.
            assessment_type: Optional assessment type filter.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (grades list, total count).
        """
        stmt = select(Grade).where(
            and_(
                Grade.student_id == student_id,
                Grade.school_id == school_id,
                Grade.deleted_at.is_(None),
            )
        )

        if class_id is not None:
            stmt = stmt.where(Grade.class_id == class_id)
        if assessment_type is not None:
            stmt = stmt.where(Grade.assessment_type == assessment_type)

        total = await self.count(stmt)

        order_col = getattr(Grade, sort_by, Grade.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        grades = await self.execute_query(stmt)
        return grades, total

    async def list_by_class(
        self,
        class_id: UUID,
        school_id: UUID,
        assessment_type: AssessmentType | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Grade], int]:
        """
        List all grades for a class with optional assessment type filter.

        Args:
            class_id: The class UUID.
            school_id: The school UUID for isolation.
            assessment_type: Optional filter.
            offset: Pagination offset.
            limit: Maximum records to return.

        Returns:
            Tuple of (grades list, total count).
        """
        stmt = select(Grade).where(
            and_(
                Grade.class_id == class_id,
                Grade.school_id == school_id,
                Grade.deleted_at.is_(None),
            )
        )

        if assessment_type is not None:
            stmt = stmt.where(Grade.assessment_type == assessment_type)

        total = await self.count(stmt)
        stmt = stmt.order_by(Grade.created_at.desc()).offset(offset).limit(limit)
        grades = await self.execute_query(stmt)
        return grades, total

    async def get_student_statistics(
        self,
        student_id: UUID,
        school_id: UUID,
        class_id: UUID | None = None,
    ) -> dict[str, float | int]:
        """
        Compute aggregate grade statistics for a student.

        Args:
            student_id: The student's UUID.
            school_id: The school UUID for isolation.
            class_id: Optional class to scope the stats.

        Returns:
            Dict with avg_score, max_score, min_score, total_grades.
        """
        stmt = select(
            func.avg(Grade.score).label("avg_score"),
            func.max(Grade.score).label("max_score"),
            func.min(Grade.score).label("min_score"),
            func.count(Grade.id).label("total_grades"),
        ).where(
            and_(
                Grade.student_id == student_id,
                Grade.school_id == school_id,
                Grade.deleted_at.is_(None),
            )
        )

        if class_id is not None:
            stmt = stmt.where(Grade.class_id == class_id)

        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "avg_score": float(row.avg_score or 0),
            "max_score": float(row.max_score or 0),
            "min_score": float(row.min_score or 0),
            "total_grades": int(row.total_grades or 0),
        }
