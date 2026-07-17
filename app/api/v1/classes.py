"""EduCore AI Platform — Classes Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_class_service, require_school_admin, require_teacher
from app.models.user import User
from app.schemas.class_ import AssignTeacherRequest, ClassCreateRequest, ClassUpdateRequest
from app.services.class_ import ClassService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/classes", tags=["Classes"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Create class")
async def create_class(
    school_id: UUID,
    payload: ClassCreateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: ClassService = Depends(get_class_service),
) -> dict:
    classroom = await service.create_class(school_id, payload, requesting_user)
    return success_response(data=classroom.model_dump(), message="Class created.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List classes")
async def list_classes(
    school_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    teacher_id: UUID | None = Query(None),
    academic_year: str | None = Query(None),
    is_active: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_teacher),
    service: ClassService = Depends(get_class_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_classes(
        school_id, params, requesting_user,
        search=search, teacher_id=teacher_id,
        academic_year=academic_year, is_active=is_active,
    )
    return success_response(data=result.model_dump(), message="Classes retrieved.")


@router.get("/{class_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get class")
async def get_class(
    school_id: UUID,
    class_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: ClassService = Depends(get_class_service),
) -> dict:
    classroom = await service.get_class(school_id, class_id, requesting_user)
    return success_response(data=classroom.model_dump(), message="Class retrieved.")


@router.patch("/{class_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update class")
async def update_class(
    school_id: UUID,
    class_id: UUID,
    payload: ClassUpdateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: ClassService = Depends(get_class_service),
) -> dict:
    classroom = await service.update_class(school_id, class_id, payload, requesting_user)
    return success_response(data=classroom.model_dump(), message="Class updated.")


@router.post("/{class_id}/assign-teacher", response_model=dict, status_code=status.HTTP_200_OK, summary="Assign teacher")
async def assign_teacher(
    school_id: UUID,
    class_id: UUID,
    payload: AssignTeacherRequest,
    requesting_user: User = Depends(require_school_admin),
    service: ClassService = Depends(get_class_service),
) -> dict:
    classroom = await service.assign_teacher(school_id, class_id, payload, requesting_user)
    return success_response(data=classroom.model_dump(), message="Teacher assigned.")


@router.delete("/{class_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Delete class")
async def delete_class(
    school_id: UUID,
    class_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: ClassService = Depends(get_class_service),
) -> dict:
    await service.delete_class(school_id, class_id, requesting_user)
    return success_response(message="Class deleted.")
