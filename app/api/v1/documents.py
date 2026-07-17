"""EduCore AI Platform — Documents Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_document_service, require_school_admin, require_teacher
from app.models.document import DocumentCategory
from app.models.user import User
from app.schemas.document import DocumentCreateRequest, DocumentUpdateRequest
from app.services.document import DocumentService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/documents", tags=["Documents"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Upload document metadata")
async def create_document(
    school_id: UUID,
    payload: DocumentCreateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    document = await service.create_document(school_id, payload, requesting_user)
    return success_response(data=document.model_dump(), message="Document registered.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List documents")
async def list_documents(
    school_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    category: DocumentCategory | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_teacher),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_documents(school_id, params, requesting_user, search=search, category=category)
    return success_response(data=result.model_dump(), message="Documents retrieved.")


@router.get("/{document_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get document")
async def get_document(
    school_id: UUID,
    document_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    document = await service.get_document(school_id, document_id, requesting_user)
    return success_response(data=document.model_dump(), message="Document retrieved.")


@router.patch("/{document_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update document metadata")
async def update_document(
    school_id: UUID,
    document_id: UUID,
    payload: DocumentUpdateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    document = await service.update_document(school_id, document_id, payload, requesting_user)
    return success_response(data=document.model_dump(), message="Document updated.")


@router.delete("/{document_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Delete document")
async def delete_document(
    school_id: UUID,
    document_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    await service.delete_document(school_id, document_id, requesting_user)
    return success_response(message="Document deleted.")
