"""EduCore AI Platform — Students Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_student_service,
    require_school_admin,
    require_teacher,
)
from app.models.user import User
from app.schemas.student import StudentCreateRequest, StudentUpdateRequest
from app.services.student import StudentService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/students", tags=["Students"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Create student")
async def create_student(
    school_id: UUID,
    payload: StudentCreateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = await service.create_student(school_id, payload, requesting_user)
    return success_response(data=student.model_dump(), message="Student created.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List students")
async def list_students(
    school_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_students(school_id, params, requesting_user, search=search)
    return success_response(data=result.model_dump(), message="Students retrieved.")


@router.get("/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get student")
async def get_student(
    school_id: UUID,
    student_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = await service.get_student(school_id, student_id, requesting_user)
    return success_response(data=student.model_dump(), message="Student retrieved.")


@router.patch("/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update student")
async def update_student(
    school_id: UUID,
    student_id: UUID,
    payload: StudentUpdateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: StudentService = Depends(get_student_service),
) -> dict:
    student = await service.update_student(school_id, student_id, payload, requesting_user)
    return success_response(data=student.model_dump(), message="Student updated.")


@router.delete("/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Delete student")
async def delete_student(
    school_id: UUID,
    student_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: StudentService = Depends(get_student_service),
) -> dict:
    await service.delete_student(school_id, student_id, requesting_user)
    return success_response(message="Student deleted.")
