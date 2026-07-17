"""
EduCore AI Platform — Base Repository

Provides a generic async CRUD base that all module repositories extend.
Repositories are the ONLY layer allowed to interact with SQLAlchemy.
Business logic MUST NOT appear here.
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository providing common CRUD operations.

    All module repositories inherit from this class and receive a
    SQLAlchemy AsyncSession via dependency injection.

    Args:
        model: The SQLAlchemy ORM model class this repository manages.
        session: The async database session for this request.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, record_id: UUID) -> ModelType | None:
        """
        Retrieve a single record by primary key.

        Args:
            record_id: The UUID primary key to look up.

        Returns:
            The matching model instance, or None if not found.
        """
        return await self.session.get(self.model, record_id)

    async def create(self, instance: ModelType) -> ModelType:
        """
        Persist a new model instance to the database.

        Args:
            instance: A fully constructed model instance.

        Returns:
            The persisted instance (with generated fields populated).
        """
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, record_id: UUID, data: dict[str, Any]) -> ModelType:
        """
        Update a record by its primary key.

        Fetches the record, applies the field updates, then flushes.
        Only non-None values in `data` are applied.

        Args:
            record_id: The UUID of the record to update.
            data: Dictionary of field names to new values.

        Returns:
            The updated instance.

        Raises:
            ValueError: If the record does not exist.
        """
        instance = await self.session.get(self.model, record_id)
        if instance is None:
            raise ValueError(f"{self.model.__name__} with id={record_id} not found.")

        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, record_id: UUID) -> None:
        """
        Mark a record as deleted by setting its deleted_at timestamp.

        This is the preferred deletion method for all business entities.
        The record remains in the database for audit and history purposes.

        Args:
            record_id: The UUID of the record to soft-delete.

        Raises:
            ValueError: If the record does not exist or lacks a deleted_at column.
        """
        instance = await self.session.get(self.model, record_id)
        if instance is None:
            raise ValueError(f"{self.model.__name__} with id={record_id} not found.")
        if not hasattr(instance, "deleted_at"):
            raise ValueError(f"{self.model.__name__} does not support soft delete.")
        instance.deleted_at = datetime.now(UTC)  # type: ignore[assignment]
        await self.session.flush()

    async def hard_delete(self, instance: ModelType) -> None:
        """
        Permanently remove a record from the database.

        Note: For business entities, prefer soft_delete(). Use this ONLY for
        technical records such as expired tokens.

        Args:
            instance: The model instance to delete.
        """
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self, stmt: Select) -> int:  # type: ignore[type-arg]
        """
        Execute a count query derived from a SELECT statement.

        Args:
            stmt: A SQLAlchemy select statement to count rows from.

        Returns:
            Total count of matching records.
        """
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()

    async def execute_query(self, stmt: Select) -> list[ModelType]:  # type: ignore[type-arg]
        """
        Execute a select statement and return all results as a list.

        Args:
            stmt: A SQLAlchemy select statement.

        Returns:
            List of model instances matching the query.
        """
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.session.rollback()
