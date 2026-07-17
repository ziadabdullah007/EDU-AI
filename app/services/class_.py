"""
EduCore AI Platform — Class Service

Business Rules:
- Class capacity cannot be exceeded.
- Only active teachers can be assigned to a class.
- Classes belong to exactly one school.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import (
    BadRequestException,
    ClassCapacityExceededException,
    ForbiddenException,
    NotFoundException,
)
from app.models.class_ import Class
from app.models.user import User, UserRole
from app.repositories.class_ import ClassRepository
from app.repositories.teacher import TeacherRepository
from app.schemas.class_ import (
    AssignTeacherRequest,
    ClassCreateRequest,
    ClassResponse,
    ClassUpdateRequest,
    ClassWithEnrollmentCountResponse
)
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class ClassService:
    """Service for classroom management operations."""

    def __init__(
        self,
        class_repo: ClassRepository,
        teacher_repo: TeacherRepository,
    ) -> None:
        self._class_repo = class_repo
        self._teacher_repo = teacher_repo

    def _assert_school_access(self, school_id: UUID, requesting_user: User) -> None:
        """Raise ForbiddenException if user cannot access the given school."""
        if requesting_user.role == UserRole.SUPER_ADMIN:
            return
        if requesting_user.school_id != school_id:
            raise ForbiddenException("Access denied to this school's class data.")

    async def create_class(
        self, school_id: UUID, payload: ClassCreateRequest, requesting_user: User
    ) -> ClassResponse:
        """Create a new classroom within a school."""
        self._assert_school_access(school_id, requesting_user)

        if payload.teacher_id is not None:
            teacher = await self._teacher_repo.get_active_by_id(payload.teacher_id, school_id)
            if teacher is None:
                raise NotFoundException(f"Teacher '{payload.teacher_id}' not found or inactive.")
            if not teacher.is_active:
                raise BadRequestException("Cannot assign an inactive teacher to a class.")

        classroom = Class(
            school_id=school_id,
            name=payload.name,
            grade_level=payload.grade_level,
            academic_year=payload.academic_year,
            capacity=payload.capacity,
            teacher_id=payload.teacher_id,
        )
        created = await self._class_repo.create(classroom)
        logger.info("class_created", class_id=str(created.id), school_id=str(school_id))
        return ClassResponse.model_validate(created)

    async def get_class(
        self, school_id: UUID, class_id: UUID, requesting_user: User
    ) -> ClassWithEnrollmentCountResponse:
        """Return a class record scoped to the school."""
        self._assert_school_access(school_id, requesting_user)

        classroom = await self._class_repo.get_active_by_id(class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{class_id}' not found.")

        enrollment_count = await self._class_repo.get_enrollment_count(class_id)

        return ClassWithEnrollmentCountResponse(
        **ClassResponse.model_validate(classroom).model_dump(),
        enrolled_count=enrollment_count,
        available_slots=classroom.capacity - enrollment_count,
    )

    async def update_class(
        self,
        school_id: UUID,
        class_id: UUID,
        payload: ClassUpdateRequest,
        requesting_user: User,
    ) -> ClassResponse:
        """Update class fields."""
        self._assert_school_access(school_id, requesting_user)
        classroom = await self._class_repo.get_active_by_id(class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{class_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)

        if "capacity" in updates:
            current_enrollment = await self._class_repo.get_enrollment_count(class_id)
            if updates["capacity"] < current_enrollment:
                raise ClassCapacityExceededException(
                    f"New capacity ({updates['capacity']}) is less than current enrollment ({current_enrollment})."
                )

        updated = await self._class_repo.update(class_id, updates)
        logger.info("class_updated", class_id=str(class_id))
        return ClassResponse.model_validate(updated)

    async def assign_teacher(
        self,
        school_id: UUID,
        class_id: UUID,
        payload: AssignTeacherRequest,
        requesting_user: User,
    ) -> ClassResponse:
        """Assign an active teacher to a class."""
        self._assert_school_access(school_id, requesting_user)
        classroom = await self._class_repo.get_active_by_id(class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{class_id}' not found.")

        teacher = await self._teacher_repo.get_active_by_id(payload.teacher_id, school_id)
        if teacher is None:
            raise NotFoundException(f"Teacher '{payload.teacher_id}' not found.")
        if not teacher.is_active:
            raise BadRequestException("Cannot assign an inactive teacher.")

        updated = await self._class_repo.update(class_id, {"teacher_id": payload.teacher_id})
        logger.info(
            "teacher_assigned_to_class",
            class_id=str(class_id),
            teacher_id=str(payload.teacher_id),
        )
        return ClassResponse.model_validate(updated)

    async def delete_class(
        self, school_id: UUID, class_id: UUID, requesting_user: User
    ) -> None:
        """Soft-delete a class."""
        self._assert_school_access(school_id, requesting_user)
        classroom = await self._class_repo.get_active_by_id(class_id, school_id)
        if classroom is None:
            raise NotFoundException(f"Class '{class_id}' not found.")
        await self._class_repo.soft_delete(class_id)
        logger.info("class_deleted", class_id=str(class_id))

    async def list_classes(
        self,
        school_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        search: str | None = None,
        teacher_id: UUID | None = None,
        academic_year: str | None = None,
        is_active: bool | None = None,
    ) -> PaginatedResponse[ClassResponse]:
        """List classes with pagination and filters."""
        self._assert_school_access(school_id, requesting_user)
        classes, total = await self._class_repo.list_classes(
            school_id=school_id,
            search=search,
            teacher_id=teacher_id,
            academic_year=academic_year,
            is_active=is_active,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [ClassResponse.model_validate(c) for c in classes]
        return build_paginated_response(items, total, params)
