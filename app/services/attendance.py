"""
EduCore AI Platform — Attendance Service

Business Rules:
- One attendance record per student per day.
- Only the assigned teacher (or admin) may record attendance.
- Bulk mark skips duplicates gracefully.
"""

from datetime import date
from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User, UserRole
from app.repositories.attendance import AttendanceRepository
from app.repositories.class_ import ClassRepository
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.attendance import (
    AttendanceSummaryResponse,
    BulkMarkAttendanceRequest,
    MarkAttendanceRequest,
    UpdateAttendanceRequest,
    AttendanceResponse,
)
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class AttendanceService:
    """Service for daily attendance management."""

    def __init__(
        self,
        attendance_repo: AttendanceRepository,
        enrollment_repo: EnrollmentRepository,
        class_repo: ClassRepository,
    ) -> None:
        self._attendance_repo = attendance_repo
        self._enrollment_repo = enrollment_repo
        self._class_repo = class_repo

    def _assert_teacher_owns_class(self, classroom, requesting_user: User) -> None:
        """Only the assigned teacher or admin may record attendance."""
        if requesting_user.role in (UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN):
            return
        if requesting_user.role == UserRole.TEACHER:
            if classroom.teacher_id != requesting_user.id:
                raise ForbiddenException("You are not assigned to this class.")

    async def mark_attendance(
        self,
        school_id: UUID,
        payload: MarkAttendanceRequest,
        requesting_user: User,
    ) -> AttendanceResponse:
        """
        Mark attendance for a single student on a given date.

        Business Rules:
        - Student must be actively enrolled in the class.
        - No duplicate record for the same student+date.
        """
        classroom = await self._class_repo.get_active_by_id(payload.class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{payload.class_id}' not found.")

        self._assert_teacher_owns_class(classroom, requesting_user)

        enrollment = await self._enrollment_repo.get_active_enrollment(payload.student_id)
        if enrollment is None or enrollment.class_id != payload.class_id:
            raise ForbiddenException("Student is not actively enrolled in this class.")

        existing = await self._attendance_repo.get_by_student_and_date(
            payload.student_id, payload.date
        )
        if existing is not None:
            raise ConflictException(
                f"Attendance already recorded for this student on {payload.date}."
            )

        record = Attendance(
            student_id=payload.student_id,
            class_id=payload.class_id,
            date=payload.date,
            status=payload.status,
            notes=payload.notes,
            recorded_by=requesting_user.id,
        )
        created = await self._attendance_repo.create(record)
        logger.info(
            "attendance_marked",
            student_id=str(payload.student_id),
            date=str(payload.date),
            status=payload.status,
        )
        return AttendanceResponse.model_validate(created)

    async def bulk_mark_attendance(
        self,
        school_id: UUID,
        payload: BulkMarkAttendanceRequest,
        requesting_user: User,
    ) -> list[AttendanceResponse]:
        """
        Mark attendance for multiple students in a class at once.

        Duplicate records are silently skipped to allow partial re-submission.
        """
        classroom = await self._class_repo.get_active_by_id(payload.class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{payload.class_id}' not found.")

        self._assert_teacher_owns_class(classroom, requesting_user)

        results: list[AttendanceResponse] = []
        for entry in payload.records:
            existing = await self._attendance_repo.get_by_student_and_date(
                entry.student_id, payload.date
            )
            if existing is not None:
                continue  # Skip duplicates gracefully in bulk mode

            record = Attendance(
                student_id=entry.student_id,
                class_id=payload.class_id,
                date=payload.date,
                status=entry.status,
                notes=entry.notes,
                recorded_by=requesting_user.id,
            )
            created = await self._attendance_repo.create(record)
            results.append(AttendanceResponse.model_validate(created))

        logger.info(
            "bulk_attendance_marked",
            class_id=str(payload.class_id),
            date=str(payload.date),
            count=len(results),
        )
        return results

    async def update_attendance(
        self,
        school_id: UUID,
        attendance_id: UUID,
        payload: UpdateAttendanceRequest,
        requesting_user: User,
    ) -> AttendanceResponse:
        """Update an existing attendance record's status or notes."""
        record = await self._attendance_repo.get(attendance_id)
        if record is None:
            raise NotFoundException(f"Attendance record '{attendance_id}' not found.")

        classroom = await self._class_repo.get_active_by_id(record.class_id, school_id)
        if classroom is None:
            raise NotFoundException("Associated class not found in this school.")

        self._assert_teacher_owns_class(classroom, requesting_user)

        updates = payload.model_dump(exclude_unset=True)
        updated = await self._attendance_repo.update(attendance_id, updates)
        return AttendanceResponse.model_validate(updated)

    async def get_student_attendance_summary(
        self,
        school_id: UUID,
        student_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> AttendanceSummaryResponse:
        """
        Return attendance summary statistics for a student.

        Attendance rate = present / total * 100 (rounded to 2 dp).
        """
        summary = await self._attendance_repo.get_student_summary(
            student_id, from_date, to_date
        )
        present = summary.get(AttendanceStatus.PRESENT.value, 0)
        absent = summary.get(AttendanceStatus.ABSENT.value, 0)
        late = summary.get(AttendanceStatus.LATE.value, 0)
        excused = summary.get(AttendanceStatus.EXCUSED.value, 0)
        total = present + absent + late + excused

        return AttendanceSummaryResponse(
            student_id=student_id,
            total_days=total,
            present=present,
            absent=absent,
            late=late,
            excused=excused,
            attendance_rate=round(present / total * 100, 2) if total > 0 else 0.0,
        )

    async def list_student_attendance(
        self,
        school_id: UUID,
        student_id: UUID,
        params: PaginationParams,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> PaginatedResponse[AttendanceResponse]:
        """Return paginated attendance records for a student."""
        records, total = await self._attendance_repo.list_by_student(
            student_id=student_id,
            from_date=from_date,
            to_date=to_date,
            offset=params.offset,
            limit=params.page_size,
        )
        items = [AttendanceResponse.model_validate(r) for r in records]
        return build_paginated_response(items, total, params)
