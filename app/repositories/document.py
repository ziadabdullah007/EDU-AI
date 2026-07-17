"""
EduCore AI Platform — Document Repository

Handles all database operations for Document metadata records.
No business logic. Only queries and persistence.

Note: Actual file content is stored externally. Only metadata is persisted here.
"""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentCategory
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Document, session)

    async def get_active_by_id(
        self, document_id: UUID, school_id: UUID
    ) -> Document | None:
        """
        Return an active document scoped to a specific school.

        Args:
            document_id: The document UUID.
            school_id: The school UUID for isolation.

        Returns:
            The Document or None.
        """
        stmt = select(Document).where(
            and_(
                Document.id == document_id,
                Document.school_id == school_id,
                Document.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_school(
        self,
        school_id: UUID,
        search: str | None = None,
        category: DocumentCategory | None = None,
        uploaded_by: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Document], int]:
        """
        List documents for a school with optional filters.

        Args:
            school_id: The school UUID for isolation.
            search: Optional text search on title and description.
            category: Optional category filter.
            uploaded_by: Optional uploader user filter.
            offset: Pagination offset.
            limit: Maximum records to return.
            sort_by: Column to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (documents list, total count).
        """
        stmt = select(Document).where(
            and_(
                Document.school_id == school_id,
                Document.deleted_at.is_(None),
            )
        )

        if search:
            stmt = stmt.where(
                or_(
                    Document.title.ilike(f"%{search}%"),
                    Document.description.ilike(f"%{search}%"),
                )
            )

        if category is not None:
            stmt = stmt.where(Document.category == category)

        if uploaded_by is not None:
            stmt = stmt.where(Document.uploaded_by == uploaded_by)

        total = await self.count(stmt)

        order_col = getattr(Document, sort_by, Document.created_at)
        stmt = stmt.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        ).offset(offset).limit(limit)

        documents = await self.execute_query(stmt)
        return documents, total

    async def title_exists_in_school(
        self, title: str, school_id: UUID, exclude_id: UUID | None = None
    ) -> bool:
        """
        Check if a document title already exists in the school.

        Args:
            title: The document title to check.
            school_id: The school to scope the check.
            exclude_id: Optional document ID to exclude (for updates).

        Returns:
            True if a document with this title already exists.
        """
        stmt = select(Document.id).where(
            and_(
                Document.title == title,
                Document.school_id == school_id,
                Document.deleted_at.is_(None),
            )
        )

        if exclude_id is not None:
            stmt = stmt.where(Document.id != exclude_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
