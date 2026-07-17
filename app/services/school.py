"""
EduCore AI Platform — School Service

Contains all school management business logic.

Business Rules:
- School names must be unique on the platform.
- School deletion is soft delete only.
- Data isolation: every sub-entity must be scoped to one school.
"""

from uuid import UUID

from app.core.logging import get_logger
from app.exceptions.errors import ConflictException, NotFoundException
from app.models.school import School
from app.models.user import User
from app.repositories.school import SchoolRepository
from app.schemas.school import SchoolCreateRequest, SchoolResponse, SchoolUpdateRequest
from app.utils.pagination import PaginationParams, build_paginated_response, PaginatedResponse

logger = get_logger(__name__)


class SchoolService:
    """Service for all school management operations."""

    def __init__(self, school_repo: SchoolRepository) -> None:
        self._school_repo = school_repo

    async def create_school(
        self, payload: SchoolCreateRequest, requesting_user: User
    ) -> SchoolResponse:
        """
        Create a new school on the platform.

        Business Rules:
        - School name must be unique.
        - Only SUPER_ADMIN may create schools.

        Args:
            payload: Validated school creation request.
            requesting_user: The authenticated SUPER_ADMIN.

        Returns:
            SchoolResponse for the created school.

        Raises:
            ConflictException: If a school with the same name already exists.
        """
        existing = await self._school_repo.get_by_name(payload.name)
        if existing is not None:
            raise ConflictException(
                f"A school named '{payload.name}' already exists."
            )

        school = School(
            name=payload.name,
            address=payload.address,
            phone=payload.phone,
            email=payload.email,
            website=payload.website,
            logo_url=payload.logo_url,
        )
        created = await self._school_repo.create(school)

        logger.info(
            "school_created",
            school_id=str(created.id),
            name=created.name,
            by=str(requesting_user.id),
        )
        return SchoolResponse.model_validate(created)

    async def get_school(self, school_id: UUID) -> SchoolResponse:
        """
        Return a school's details by its ID.

        Args:
            school_id: The school UUID.

        Returns:
            SchoolResponse.

        Raises:
            NotFoundException: If the school does not exist.
        """
        school = await self._school_repo.get(school_id)
        if school is None or school.deleted_at is not None:
            raise NotFoundException(f"School with ID '{school_id}' not found.")
        return SchoolResponse.model_validate(school)

    async def update_school(
        self,
        school_id: UUID,
        payload: SchoolUpdateRequest,
        requesting_user: User,
    ) -> SchoolResponse:
        """
        Update school information.

        Business Rules:
        - If changing the name, the new name must not conflict.
        - SCHOOL_ADMIN can only update their own school.

        Args:
            school_id: The school to update.
            payload: Fields to update (all optional).
            requesting_user: The authenticated user.

        Returns:
            Updated SchoolResponse.

        Raises:
            NotFoundException: If the school does not exist.
            ConflictException: If the new name is already taken.
        """
        school = await self._school_repo.get(school_id)
        if school is None or school.deleted_at is not None:
            raise NotFoundException(f"School with ID '{school_id}' not found.")

        updates = payload.model_dump(exclude_unset=True)

        if "name" in updates and updates["name"] != school.name:
            existing = await self._school_repo.get_by_name(updates["name"])
            if existing is not None and existing.id != school_id:
                raise ConflictException(
                    f"A school named '{updates['name']}' already exists."
                )

        updated = await self._school_repo.update(school_id, updates)
        logger.info("school_updated", school_id=str(school_id), by=str(requesting_user.id))
        return SchoolResponse.model_validate(updated)

    async def deactivate_school(
        self, school_id: UUID, requesting_user: User
    ) -> None:
        """
        Soft-delete a school.

        Business Rules:
        - Uses soft delete (sets deleted_at).
        - Only SUPER_ADMIN can deactivate schools.

        Args:
            school_id: The school UUID.
            requesting_user: The requesting SUPER_ADMIN.

        Raises:
            NotFoundException: If the school does not exist.
        """
        school = await self._school_repo.get(school_id)
        if school is None or school.deleted_at is not None:
            raise NotFoundException(f"School with ID '{school_id}' not found.")

        await self._school_repo.soft_delete(school_id)
        logger.info(
            "school_deactivated",
            school_id=str(school_id),
            by=str(requesting_user.id),
        )

    async def list_schools(
        self,
        params: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> PaginatedResponse[SchoolResponse]:
        """
        List all schools with pagination, search, and filtering.

        Args:
            params: Pagination parameters (page, page_size, sort_by, sort_order).
            search: Optional text search on school name.
            is_active: Optional filter for active/inactive schools.

        Returns:
            PaginatedResponse containing school records.
        """
        schools, total = await self._school_repo.list_schools(
            search=search,
            is_active=is_active,
            offset=params.offset,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        items = [SchoolResponse.model_validate(s) for s in schools]
        return build_paginated_response(items, total, params)
