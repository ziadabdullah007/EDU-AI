"""
EduCore AI Platform — Document Service

Business Rules:
- Only metadata is stored; files are stored externally.
- Soft delete is used for document records.
- Future AI: RAG, Knowledge Search, AI Assistant.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import ConflictException, ForbiddenException, NotFoundException
from app.models.document import Document, DocumentCategory
from app.models.user import User, UserRole
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentCreateRequest, DocumentResponse, DocumentUpdateRequest
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class DocumentService:
    """Service for school document metadata management."""

    def __init__(self, document_repo: DocumentRepository) -> None:
        self._document_repo = document_repo

    def _assert_school_access(self, school_id: UUID, requesting_user: User) -> None:
        if requesting_user.role == UserRole.SUPER_ADMIN:
            return
        if requesting_user.school_id != school_id:
            raise ForbiddenException("Access denied to this school's documents.")

    async def create_document(
        self,
        school_id: UUID,
        payload: DocumentCreateRequest,
        requesting_user: User,
    ) -> DocumentResponse:
        """Register document metadata for a school."""
        self._assert_school_access(school_id, requesting_user)

        if await self._document_repo.title_exists_in_school(payload.title, school_id):
            raise ConflictException(
                f"A document named '{payload.title}' already exists in this school."
            )

        document = Document(
            school_id=school_id,
            uploaded_by=requesting_user.id,
            title=payload.title,
            description=payload.description,
            file_url=payload.file_url,
            file_type=payload.file_type,
            file_size_bytes=payload.file_size_bytes,
            category=payload.category,
        )
        created = await self._document_repo.create(document)
        logger.info("document_created", document_id=str(created.id), school_id=str(school_id))
        return DocumentResponse.model_validate(created)

    async def get_document(
        self, school_id: UUID, document_id: UUID, requesting_user: User
    ) -> DocumentResponse:
        """Return a document by ID."""
        self._assert_school_access(school_id, requesting_user)
        document = await self._document_repo.get_active_by_id(document_id, school_id)
        if document is None:
            raise NotFoundException(f"Document '{document_id}' not found.")
        return DocumentResponse.model_validate(document)

    async def update_document(
        self,
        school_id: UUID,
        document_id: UUID,
        payload: DocumentUpdateRequest,
        requesting_user: User,
    ) -> DocumentResponse:
        """Update document metadata."""
        self._assert_school_access(school_id, requesting_user)
        document = await self._document_repo.get_active_by_id(document_id, school_id)
        if document is None:
            raise NotFoundException(f"Document '{document_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)
        if "title" in updates and updates["title"] != document.title:
            if await self._document_repo.title_exists_in_school(
                updates["title"], school_id, exclude_id=document_id
            ):
                raise ConflictException(
                    f"A document named '{updates['title']}' already exists."
                )

        updated = await self._document_repo.update(document_id, updates)
        logger.info("document_updated", document_id=str(document_id))
        return DocumentResponse.model_validate(updated)

    async def delete_document(
        self, school_id: UUID, document_id: UUID, requesting_user: User
    ) -> None:
        """Soft-delete a document metadata record."""
        self._assert_school_access(school_id, requesting_user)
        document = await self._document_repo.get_active_by_id(document_id, school_id)
        if document is None:
            raise NotFoundException(f"Document '{document_id}' not found.")
        await self._document_repo.soft_delete(document_id)
        logger.info("document_deleted", document_id=str(document_id))

    async def list_documents(
        self,
        school_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        search: str | None = None,
        category: DocumentCategory | None = None,
        uploaded_by: UUID | None = None,
    ) -> PaginatedResponse[DocumentResponse]:
        """List documents with pagination and filters."""
        self._assert_school_access(school_id, requesting_user)
        documents, total = await self._document_repo.list_by_school(
            school_id=school_id,
            search=search,
            category=category,
            uploaded_by=uploaded_by,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [DocumentResponse.model_validate(d) for d in documents]
        return build_paginated_response(items, total, params)
