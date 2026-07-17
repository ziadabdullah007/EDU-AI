"""EduCore AI Platform — Grades Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_grade_service, require_school_admin, require_teacher
from app.models.grade import AssessmentType
from app.models.user import User
from app.schemas.grade import AddGradeRequest, UpdateGradeRequest
from app.services.grade import GradeService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/grades", tags=["Grades"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Add grade")
async def add_grade(
    school_id: UUID,
    payload: AddGradeRequest,
    requesting_user: User = Depends(require_teacher),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    grade = await service.add_grade(school_id, payload, requesting_user)
    return success_response(data=grade.model_dump(), message="Grade added.")


@router.get("/students/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Student grades")
async def list_student_grades(
    school_id: UUID,
    student_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    class_id: UUID | None = Query(None),
    assessment_type: AssessmentType | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_teacher),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_student_grades(school_id, student_id, params, class_id, assessment_type)
    return success_response(data=result.model_dump(), message="Grades retrieved.")


@router.get("/students/{student_id}/statistics", response_model=dict, status_code=status.HTTP_200_OK, summary="Grade statistics")
async def get_grade_statistics(
    school_id: UUID,
    student_id: UUID,
    class_id: UUID | None = Query(None),
    requesting_user: User = Depends(require_teacher),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    stats = await service.get_student_grade_statistics(school_id, student_id, class_id)
    return success_response(data=stats.model_dump(), message="Statistics retrieved.")


@router.get("/classes/{class_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Class grades")
async def list_class_grades(
    school_id: UUID,
    class_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    assessment_type: AssessmentType | None = Query(None),
    requesting_user: User = Depends(require_teacher),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size)
    result = await service.list_class_grades(school_id, class_id, params, assessment_type)
    return success_response(data=result.model_dump(), message="Grades retrieved.")


@router.patch("/{grade_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update grade")
async def update_grade(
    school_id: UUID,
    grade_id: UUID,
    payload: UpdateGradeRequest,
    requesting_user: User = Depends(require_teacher),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    grade = await service.update_grade(school_id, grade_id, payload, requesting_user)
    return success_response(data=grade.model_dump(), message="Grade updated.")


@router.delete("/{grade_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Delete grade")
async def delete_grade(
    school_id: UUID,
    grade_id: UUID,
    requesting_user: User = Depends(require_school_admin),
    service: GradeService = Depends(get_grade_service),
) -> dict:
    await service.delete_grade(school_id, grade_id, requesting_user)
    return success_response(message="Grade deleted.")
