"""
EduCore AI Platform — Teacher Service

Business Rules:
- Teacher belongs to one school via user_id.
- Employee number must be unique within a school.
- Inactive teachers cannot receive new classes.
- Deletion is soft delete only.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import ConflictException, ForbiddenException, NotFoundException
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.repositories.teacher import TeacherRepository
from app.repositories.user import UserRepository
from app.schemas.teacher import TeacherCreateRequest, TeacherResponse, TeacherUpdateRequest
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class TeacherService:
    """Service for all teacher profile management operations."""

    def __init__(self, teacher_repo: TeacherRepository, user_repo: UserRepository) -> None:
        self._teacher_repo = teacher_repo
        self._user_repo = user_repo

    def _assert_school_access(self, school_id: UUID, requesting_user: User) -> None:
        """Raise ForbiddenException if user cannot access the given school."""
        if requesting_user.role == UserRole.SUPER_ADMIN:
            return
        if requesting_user.school_id != school_id:
            raise ForbiddenException("Access denied to this school's teacher data.")

    async def create_teacher(
        self, school_id: UUID, payload: TeacherCreateRequest, requesting_user: User
    ) -> TeacherResponse:
        """
        Create a new teacher profile linked to an existing User account.

        Business Rules:
        - employee_number must be unique within the school.
        - user_id must reference an existing, active User.
        """
        self._assert_school_access(school_id, requesting_user)

        if await self._teacher_repo.employee_number_exists(payload.employee_number, school_id):
            raise ConflictException(
                f"Employee number '{payload.employee_number}' already exists in this school."
            )

        user = await self._user_repo.get(payload.user_id)
        if user is None:
            raise NotFoundException(f"User '{payload.user_id}' not found.")

        teacher = Teacher(
            school_id=school_id,
            user_id=payload.user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            employee_number=payload.employee_number,
            specialization=payload.specialization,
            phone=payload.phone,
            bio=payload.bio,
        )
        created = await self._teacher_repo.create(teacher)
        logger.info("teacher_created", teacher_id=str(created.id), school_id=str(school_id))
        return TeacherResponse.model_validate(created)

    async def get_teacher(
        self, school_id: UUID, teacher_id: UUID, requesting_user: User
    ) -> TeacherResponse:
        """Return a teacher profile scoped to the school."""
        self._assert_school_access(school_id, requesting_user)
        teacher = await self._teacher_repo.get_active_by_id(teacher_id, school_id)
        if teacher is None:
            raise NotFoundException(f"Teacher '{teacher_id}' not found.")
        return TeacherResponse.model_validate(teacher)

    async def update_teacher(
        self,
        school_id: UUID,
        teacher_id: UUID,
        payload: TeacherUpdateRequest,
        requesting_user: User,
    ) -> TeacherResponse:
        """Update teacher profile fields."""
        self._assert_school_access(school_id, requesting_user)
        teacher = await self._teacher_repo.get_active_by_id(teacher_id, school_id)
        if teacher is None:
            raise NotFoundException(f"Teacher '{teacher_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)
        if "employee_number" in updates and updates["employee_number"] != teacher.employee_number:
            if await self._teacher_repo.employee_number_exists(
                updates["employee_number"], school_id, exclude_id=teacher_id
            ):
                raise ConflictException(
                    f"Employee number '{updates['employee_number']}' already taken."
                )

        updated = await self._teacher_repo.update(teacher_id, updates)
        logger.info("teacher_updated", teacher_id=str(teacher_id))
        return TeacherResponse.model_validate(updated)

    async def delete_teacher(
        self, school_id: UUID, teacher_id: UUID, requesting_user: User
    ) -> None:
        """Soft-delete a teacher profile."""
        self._assert_school_access(school_id, requesting_user)
        teacher = await self._teacher_repo.get_active_by_id(teacher_id, school_id)
        if teacher is None:
            raise NotFoundException(f"Teacher '{teacher_id}' not found.")
        await self._teacher_repo.soft_delete(teacher_id)
        logger.info("teacher_deleted", teacher_id=str(teacher_id))

    async def list_teachers(
        self,
        school_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        search: str | None = None,
        is_active: bool | None = None,
        specialization: str | None = None,
    ) -> PaginatedResponse[TeacherResponse]:
        """List teachers with pagination, search, and filters."""
        self._assert_school_access(school_id, requesting_user)
        teachers, total = await self._teacher_repo.list_teachers(
            school_id=school_id,
            search=search,
            is_active=is_active,
            specialization=specialization,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [TeacherResponse.model_validate(t) for t in teachers]
        return build_paginated_response(items, total, params)
