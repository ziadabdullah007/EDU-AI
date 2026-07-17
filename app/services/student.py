"""
EduCore AI Platform — Student Service

Business Rules:
- Student number must be unique within a school.
- Student belongs to exactly one school.
- Deletion is soft delete only.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import ConflictException, ForbiddenException, NotFoundException
from app.models.student import Student
from app.models.user import User, UserRole
from app.repositories.student import StudentRepository
from app.repositories.user import UserRepository
from app.schemas.student import StudentCreateRequest, StudentResponse, StudentUpdateRequest
from app.utils.pagination import PaginatedResponse, PaginationParams, build_paginated_response

logger = get_logger(__name__)


class StudentService:
    """Service for all student profile management operations."""

    def __init__(self, student_repo: StudentRepository, user_repo: UserRepository) -> None:
        self._student_repo = student_repo
        self._user_repo = user_repo

    def _assert_school_access(self, school_id: UUID, requesting_user: User) -> None:
        """Raise ForbiddenException if user cannot access the given school."""
        if requesting_user.role == UserRole.SUPER_ADMIN:
            return
        if requesting_user.school_id != school_id:
            raise ForbiddenException("Access denied to this school's student data.")

    async def create_student(
        self, school_id: UUID, payload: StudentCreateRequest, requesting_user: User
    ) -> StudentResponse:
        """Create a new student profile within a school."""
        self._assert_school_access(school_id, requesting_user)

        if await self._student_repo.student_number_exists(payload.student_number, school_id):
            raise ConflictException(
                f"Student number '{payload.student_number}' already exists in this school."
            )

        if payload.user_id is not None:
            user = await self._user_repo.get(payload.user_id)
            if user is None:
                raise NotFoundException(f"User '{payload.user_id}' not found.")

        student = Student(
            school_id=school_id,
            user_id=payload.user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            student_number=payload.student_number,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            guardian_name=payload.guardian_name,
            guardian_phone=payload.guardian_phone,
        )
        created = await self._student_repo.create(student)
        logger.info("student_created", student_id=str(created.id), school_id=str(school_id))
        return StudentResponse.model_validate(created)

    async def get_student(
        self, school_id: UUID, student_id: UUID, requesting_user: User
    ) -> StudentResponse:
        """Return a student profile scoped to the school."""
        self._assert_school_access(school_id, requesting_user)
        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")
        return StudentResponse.model_validate(student)

    async def update_student(
        self,
        school_id: UUID,
        student_id: UUID,
        payload: StudentUpdateRequest,
        requesting_user: User,
    ) -> StudentResponse:
        """Update student profile fields."""
        self._assert_school_access(school_id, requesting_user)
        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)
        if "student_number" in updates and updates["student_number"] != student.student_number:
            if await self._student_repo.student_number_exists(
                updates["student_number"], school_id, exclude_id=student_id
            ):
                raise ConflictException(
                    f"Student number '{updates['student_number']}' already taken."
                )

        updated = await self._student_repo.update(student_id, updates)
        logger.info("student_updated", student_id=str(student_id))
        return StudentResponse.model_validate(updated)

    async def delete_student(
        self, school_id: UUID, student_id: UUID, requesting_user: User
    ) -> None:
        """Soft-delete a student profile."""
        self._assert_school_access(school_id, requesting_user)
        student = await self._student_repo.get_active_by_id(student_id, school_id)
        if student is None:
            raise NotFoundException(f"Student '{student_id}' not found.")
        await self._student_repo.soft_delete(student_id)
        logger.info("student_deleted", student_id=str(student_id))

    async def list_students(
        self,
        school_id: UUID,
        params: PaginationParams,
        requesting_user: User,
        search: str | None = None,
        gender: str | None = None,
        class_id: UUID | None = None,
    ) -> PaginatedResponse[StudentResponse]:
        """List students with pagination, search, and filters."""
        self._assert_school_access(school_id, requesting_user)
        students, total = await self._student_repo.list_students(
            school_id=school_id,
            search=search,
            gender=gender,
            class_id=class_id,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [StudentResponse.model_validate(s) for s in students]
        return build_paginated_response(items, total, params)
