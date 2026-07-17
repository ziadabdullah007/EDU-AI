"""EduCore AI Platform — Attendance Router"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_attendance_service, require_school_admin, require_teacher
from app.models.user import User
from app.schemas.attendance import BulkMarkAttendanceRequest, MarkAttendanceRequest, UpdateAttendanceRequest
from app.services.attendance import AttendanceService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/attendance", tags=["Attendance"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Mark attendance")
async def mark_attendance(
    school_id: UUID,
    payload: MarkAttendanceRequest,
    requesting_user: User = Depends(require_teacher),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict:
    record = await service.mark_attendance(school_id, payload, requesting_user)
    return success_response(data=record.model_dump(), message="Attendance marked.")


@router.post("/bulk", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Bulk mark attendance")
async def bulk_mark_attendance(
    school_id: UUID,
    payload: BulkMarkAttendanceRequest,
    requesting_user: User = Depends(require_teacher),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict:
    records = await service.bulk_mark_attendance(school_id, payload, requesting_user)
    return success_response(data=[r.model_dump() for r in records], message=f"{len(records)} records marked.")


@router.patch("/{attendance_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update attendance")
async def update_attendance(
    school_id: UUID,
    attendance_id: UUID,
    payload: UpdateAttendanceRequest,
    requesting_user: User = Depends(require_teacher),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict:
    record = await service.update_attendance(school_id, attendance_id, payload, requesting_user)
    return success_response(data=record.model_dump(), message="Attendance updated.")


@router.get("/students/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Student attendance")
async def list_student_attendance(
    school_id: UUID,
    student_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    requesting_user: User = Depends(require_teacher),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size)
    result = await service.list_student_attendance(school_id, student_id, params, from_date, to_date)
    return success_response(data=result.model_dump(), message="Attendance retrieved.")


@router.get("/students/{student_id}/summary", response_model=dict, status_code=status.HTTP_200_OK, summary="Attendance summary")
async def get_attendance_summary(
    school_id: UUID,
    student_id: UUID,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    requesting_user: User = Depends(require_teacher),
    service: AttendanceService = Depends(get_attendance_service),
) -> dict:
    summary = await service.get_student_attendance_summary(school_id, student_id, from_date, to_date)
    return success_response(data=summary.model_dump(), message="Summary retrieved.")
