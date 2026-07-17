"""
EduCore AI Platform — Grade Service

Business Rules:
- score must be >= 0 and <= max_score.
- Only the assigned teacher may create grades.
- Deletion is soft delete.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import BadRequestException, ForbiddenException, NotFoundException
from app.models.grade import AssessmentType, Grade
from app.models.user import User, UserRole
from app.repositories.class_ import ClassRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.grade import GradeRepository
from app.schemas.grade import (
    AddGradeRequest,
    GradeResponse,
    GradeStatisticsResponse,
    UpdateGradeRequest,
)
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class GradeService:
    """Service for academic grade management."""

    def __init__(
        self,
        grade_repo: GradeRepository,
        enrollment_repo: EnrollmentRepository,
        class_repo: ClassRepository,
    ) -> None:
        self._grade_repo = grade_repo
        self._enrollment_repo = enrollment_repo
        self._class_repo = class_repo

    def _assert_teacher_owns_class(self, classroom, requesting_user: User) -> None:
        """Only the assigned teacher or admin may add/update grades."""
        if requesting_user.role in (UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN):
            return
        if requesting_user.role == UserRole.TEACHER:
            if classroom.teacher_id != requesting_user.id:
                raise ForbiddenException("You are not assigned to this class.")

    async def add_grade(
        self,
        school_id: UUID,
        payload: AddGradeRequest,
        requesting_user: User,
    ) -> GradeResponse:
        """
        Add a grade record for a student.

        Business Rules:
        - score must be <= max_score (enforced in schema and here).
        - Student must be actively enrolled in the class.
        - Only the assigned teacher (or admin) may submit grades.
        """
        classroom = await self._class_repo.get_active_by_id(payload.class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{payload.class_id}' not found.")

        self._assert_teacher_owns_class(classroom, requesting_user)

        enrollment = await self._enrollment_repo.get_active_enrollment(payload.student_id)
        if enrollment is None or enrollment.class_id != payload.class_id:
            raise ForbiddenException("Student is not actively enrolled in this class.")

        # Schema-level validation already ensures score <= max_score,
        # but we enforce it here too as a defence-in-depth measure.
        if payload.score > payload.max_score:
            raise BadRequestException(
                f"Score ({payload.score}) cannot exceed max_score ({payload.max_score})."
            )

        grade = Grade(
            student_id=payload.student_id,
            class_id=payload.class_id,
            school_id=school_id,
            teacher_id=requesting_user.id,
            subject=payload.subject,
            assessment_type=payload.assessment_type,
            score=payload.score,
            max_score=payload.max_score,
            term=payload.term,
            academic_year=payload.academic_year,
            notes=payload.notes,
        )
        created = await self._grade_repo.create(grade)
        logger.info(
            "grade_added",
            student_id=str(payload.student_id),
            class_id=str(payload.class_id),
            score=payload.score,
            max_score=payload.max_score,
        )
        return GradeResponse.model_validate(created)

    async def update_grade(
        self,
        school_id: UUID,
        grade_id: UUID,
        payload: UpdateGradeRequest,
        requesting_user: User,
    ) -> GradeResponse:
        """Update an existing grade record's score or notes."""
        grade = await self._grade_repo.get_active_by_id(grade_id, school_id)
        if grade is None:
            raise NotFoundException(f"Grade '{grade_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)

        new_score = updates.get("score", grade.score)
        new_max = updates.get("max_score", grade.max_score)
        if new_score > new_max:
            raise BadRequestException(
                f"Score ({new_score}) cannot exceed max_score ({new_max})."
            )

        updated = await self._grade_repo.update(grade_id, updates)
        logger.info("grade_updated", grade_id=str(grade_id))
        return GradeResponse.model_validate(updated)

    async def delete_grade(
        self, school_id: UUID, grade_id: UUID, requesting_user: User
    ) -> None:
        """Soft-delete a grade record."""
        grade = await self._grade_repo.get_active_by_id(grade_id, school_id)
        if grade is None:
            raise NotFoundException(f"Grade '{grade_id}' not found.")
        await self._grade_repo.soft_delete(grade_id)
        logger.info("grade_deleted", grade_id=str(grade_id))

    async def get_student_grade_statistics(
        self,
        school_id: UUID,
        student_id: UUID,
        class_id: UUID | None = None,
    ) -> GradeStatisticsResponse:
        """Return aggregate grade stats for a student."""
        stats = await self._grade_repo.get_student_statistics(
            student_id=student_id,
            school_id=school_id,
            class_id=class_id,
        )
        return GradeStatisticsResponse(student_id=student_id, **stats)

    async def list_student_grades(
        self,
        school_id: UUID,
        student_id: UUID,
        params: PaginationParams,
        class_id: UUID | None = None,
        assessment_type: AssessmentType | None = None,
    ) -> PaginatedResponse[GradeResponse]:
        """List grades for a student with optional filters."""
        grades, total = await self._grade_repo.list_by_student(
            student_id=student_id,
            school_id=school_id,
            class_id=class_id,
            assessment_type=assessment_type,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [GradeResponse.model_validate(g) for g in grades]
        return build_paginated_response(items, total, params)

    async def list_class_grades(
        self,
        school_id: UUID,
        class_id: UUID,
        params: PaginationParams,
        assessment_type: AssessmentType | None = None,
    ) -> PaginatedResponse[GradeResponse]:
        """List all grades for a class."""
        grades, total = await self._grade_repo.list_by_class(
            class_id=class_id,
            school_id=school_id,
            assessment_type=assessment_type,
            offset=params.offset,
            limit=params.page_size,
        )
        items = [GradeResponse.model_validate(g) for g in grades]
        return build_paginated_response(items, total, params)
