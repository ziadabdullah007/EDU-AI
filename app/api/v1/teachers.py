"""EduCore AI Platform — Teachers Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_teacher_service, require_school_admin, require_teacher
from app.models.user import User
from app.schemas.teacher import TeacherCreateRequest, TeacherUpdateRequest
from app.services.teacher import TeacherService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/teachers", tags=["Teachers"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Create teacher")
async def create_teacher(
    school_id: UUID,
    payload: TeacherCreateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: TeacherService = Depends(get_teacher_service),
) -> dict:
    teacher = await service.create_teacher(school_id, payload, requesting_user)
    return success_response(data=teacher.model_dump(), message="Teacher created.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List teachers")
async def list_teachers(
    school_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_teacher),
    service: TeacherService = Depends(get_teacher_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_teachers(school_id, params, requesting_user, search=search, is_active=is_active)
    return success_response(data=result.model_dump(), message="Teachers retrieved.")


@router.get("/{teacher_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get teacher")
async def get_teacher(
    school_id: UUID,
    teacher_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: TeacherService = Depends(get_teacher_service),
) -> dict:
    teacher = await service.get_teacher(school_id, teacher_id, requesting_user)
    return success_response(data=teacher.model_dump(), message="Teacher retrieved.")


@router.patch("/{teacher_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update teacher")
async def update_teacher(
    school_id: UUID,
    teacher_id: UUID,
    payload: TeacherUpdateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: TeacherService = Depends(get_teacher_service),
) -> dict:
    teacher = await service.update_teacher(school_id, teacher_id, payload, requesting_user)
    return success_response(data=teacher.model_dump(), message="Teacher updated.")


@router.delete("/{teacher_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Delete teacher")
async def delete_teacher(
    school_id: UUID,
    teacher_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: TeacherService = Depends(get_teacher_service),
) -> dict:
    await service.delete_teacher(school_id, teacher_id, requesting_user)
    return success_response(message="Teacher deleted.")
