"""
EduCore AI Platform — Enrollment Service

Business Rules:
- One active enrollment per student at a time.
- Transferred students keep history (status changes to TRANSFERRED).
- No duplicate active enrollment for same student+class.
- Class capacity must not be exceeded when enrolling.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import (
    ClassCapacityExceededException,
    ConflictException,
    NotFoundException,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User
from app.repositories.class_ import ClassRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.student import StudentRepository
from app.schemas.enrollment import (
    EnrollmentResponse,
    EnrollStudentRequest,
    TransferStudentRequest,
)
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class EnrollmentService:
    """Service for student enrollment and class transfer operations."""

    def __init__(
        self,
        enrollment_repo: EnrollmentRepository,
        class_repo: ClassRepository,
        student_repo: StudentRepository,
    ) -> None:
        self._enrollment_repo = enrollment_repo
        self._class_repo = class_repo
        self._student_repo = student_repo

    async def enroll_student(
        self,
        school_id: UUID,
        payload: EnrollStudentRequest,
        requesting_user: User,
    ) -> EnrollmentResponse:
        """
        Enroll a student into a class.

        Business Rules:
        - Student must not already have an active enrollment.
        - Class capacity must not be exceeded.
        - Both student and class must belong to the same school.
        """
        student = await self._student_repo.get_active_by_id(payload.student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{payload.student_id}' not found.")

        classroom = await self._class_repo.get_active_by_id(payload.class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{payload.class_id}' not found.")

        existing = await self._enrollment_repo.get_active_enrollment(payload.student_id)
        if existing is not None:
            raise ConflictException(
                f"Student is already actively enrolled in class '{existing.class_id}'."
            )

        current_count = await self._class_repo.get_enrollment_count(payload.class_id)
        if current_count >= classroom.capacity:
            raise ClassCapacityExceededException(
                f"Class has reached maximum capacity of {classroom.capacity}."
            )

        enrollment = Enrollment(
            student_id=payload.student_id,
            class_id=payload.class_id,
            status=EnrollmentStatus.ACTIVE,
        )
        created = await self._enrollment_repo.create(enrollment)
        logger.info(
            "student_enrolled",
            student_id=str(payload.student_id),
            class_id=str(payload.class_id),
        )
        return EnrollmentResponse.model_validate(created)

    async def transfer_student(
        self,
        school_id: UUID,
        enrollment_id: UUID,
        payload: TransferStudentRequest,
        requesting_user: User,
    ) -> EnrollmentResponse:
        """
        Transfer a student from their current class to a new one.

        Business Rules:
        - Current enrollment status changes to TRANSFERRED.
        - A new ACTIVE enrollment is created in the target class.
        - Target class capacity must not be exceeded.
        """
        current = await self._enrollment_repo.get_active_by_id(enrollment_id, school_id)
        if current is None or current.status != EnrollmentStatus.ACTIVE:
            raise NotFoundException("Active enrollment not found.")

        target_class = await self._class_repo.get_active_by_id(payload.target_class_id, school_id)
        if target_class is None:
            raise NotFoundException(f"Target class '{payload.target_class_id}' not found.")

        count = await self._class_repo.get_enrollment_count(payload.target_class_id)
        if count >= target_class.capacity:
            raise ClassCapacityExceededException(
                f"Target class has reached maximum capacity of {target_class.capacity}."
            )

        await self._enrollment_repo.update(
            enrollment_id, {"status": EnrollmentStatus.TRANSFERRED}
        )
        new_enrollment = Enrollment(
            student_id=current.student_id,
            class_id=payload.target_class_id,
            status=EnrollmentStatus.ACTIVE,
            notes=payload.notes,
        )
        created = await self._enrollment_repo.create(new_enrollment)
        logger.info(
            "student_transferred",
            student_id=str(current.student_id),
            from_class=str(current.class_id),
            to_class=str(payload.target_class_id),
        )
        return EnrollmentResponse.model_validate(created)

    async def remove_enrollment(
        self, school_id: UUID, enrollment_id: UUID, requesting_user: User
    ) -> None:
        """Remove a student from a class (changes status to WITHDRAWN)."""
        enrollment = await self._enrollment_repo.get_active_by_id(enrollment_id, school_id)
        if enrollment is None or enrollment.status != EnrollmentStatus.ACTIVE:
            raise NotFoundException("Active enrollment not found.")

        await self._enrollment_repo.update(
            enrollment_id, {"status": EnrollmentStatus.WITHDRAWN}
        )
        logger.info("student_withdrawn", enrollment_id=str(enrollment_id))

    async def get_enrollment_history(
        self, school_id: UUID, student_id: UUID, params: PaginationParams
    ) -> PaginatedResponse[EnrollmentResponse]:
        """Return all enrollment records (history) for a student."""
        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")

        enrollments, total = await self._enrollment_repo.list_by_student(
            student_id=student_id,
            offset=params.offset,
            limit=params.page_size,
        )
        items = [EnrollmentResponse.model_validate(e) for e in enrollments]
        return build_paginated_response(items, total, params)

    async def list_class_enrollments(
        self,
        school_id: UUID,
        class_id: UUID,
        params: PaginationParams,
        status: EnrollmentStatus | None = None,
    ) -> PaginatedResponse[EnrollmentResponse]:
        """Return all enrollments for a class."""
        classroom = await self._class_repo.get_active_by_id(class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{class_id}' not found.")

        enrollments, total = await self._enrollment_repo.list_by_class(
            class_id=class_id,
            status=status,
            offset=params.offset,
            limit=params.page_size,
        )
        items = [EnrollmentResponse.model_validate(e) for e in enrollments]
        return build_paginated_response(items, total, params)
