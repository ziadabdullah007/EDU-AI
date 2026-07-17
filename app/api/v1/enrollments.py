"""EduCore AI Platform — Enrollment Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_enrollment_service, require_school_admin, require_teacher
from app.models.enrollment import EnrollmentStatus
from app.models.user import User
from app.schemas.enrollment import EnrollStudentRequest, TransferStudentRequest
from app.services.enrollment import EnrollmentService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/enrollments", tags=["Enrollment"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Enroll student")
async def enroll_student(
    school_id: UUID,
    payload: EnrollStudentRequest,
    requesting_user: User = Depends(require_school_admin),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> dict:
    enrollment = await service.enroll_student(school_id, payload, requesting_user)
    return success_response(data=enrollment.model_dump(), message="Student enrolled.")


@router.post("/{enrollment_id}/transfer", response_model=dict, status_code=status.HTTP_200_OK, summary="Transfer student")
async def transfer_student(
    school_id: UUID,
    enrollment_id: UUID,
    payload: TransferStudentRequest,
    requesting_user: User = Depends(require_school_admin),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> dict:
    enrollment = await service.transfer_student(school_id, enrollment_id, payload, requesting_user)
    return success_response(data=enrollment.model_dump(), message="Student transferred.")


@router.delete("/{enrollment_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Remove enrollment")
async def remove_enrollment(
    school_id: UUID,
    enrollment_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> dict:
    await service.remove_enrollment(school_id, enrollment_id, requesting_user)
    return success_response(message="Student withdrawn from class.")


@router.get("/students/{student_id}/history", response_model=dict, status_code=status.HTTP_200_OK, summary="Student enrollment history")
async def get_student_history(
    school_id: UUID,
    student_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    requesting_user: User = Depends(require_teacher),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size)
    result = await service.get_enrollment_history(school_id, student_id, params)
    return success_response(data=result.model_dump(), message="Enrollment history retrieved.")


@router.get("/classes/{class_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Class enrollments")
async def list_class_enrollments(
    school_id: UUID,
    class_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EnrollmentStatus | None = Query(None, alias="status"),
    requesting_user: User = Depends(require_teacher),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size)
    result = await service.list_class_enrollments(school_id, class_id, params, status=status_filter)
    return success_response(data=result.model_dump(), message="Class enrollments retrieved.")
