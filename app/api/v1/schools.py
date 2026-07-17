"""EduCore AI Platform — Schools Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_school_service, require_school_admin, require_super_admin
from app.models.user import User
from app.schemas.school import SchoolCreateRequest, SchoolUpdateRequest
from app.services.school import SchoolService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Create a school")
async def create_school(
    payload: SchoolCreateRequest,
    requesting_user: User = Depends(require_super_admin),
    service: SchoolService = Depends(get_school_service),
) -> dict:
    school = await service.create_school(payload, requesting_user)
    return success_response(data=school.model_dump(), message="School created successfully.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List schools")
async def list_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    _: User = Depends(require_super_admin),
    service: SchoolService = Depends(get_school_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_schools(params, search=search, is_active=is_active)
    return success_response(data=result.model_dump(), message="Schools retrieved.")


@router.get("/{school_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get school details")
async def get_school(
    school_id: UUID,
    _: User = Depends(require_school_admin),
    service: SchoolService = Depends(get_school_service),
) -> dict:
    school = await service.get_school(school_id)
    return success_response(data=school.model_dump(), message="School retrieved.")


@router.patch("/{school_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update school")
async def update_school(
    school_id: UUID,
    payload: SchoolUpdateRequest,
    requesting_user: User = Depends(require_school_admin),
    service: SchoolService = Depends(get_school_service),
) -> dict:
    school = await service.update_school(school_id, payload, requesting_user)
    return success_response(data=school.model_dump(), message="School updated.")


@router.delete("/{school_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Deactivate school")
async def deactivate_school(
    school_id: UUID,
    requesting_user: User = Depends(require_super_admin),
    service: SchoolService = Depends(get_school_service),
) -> dict:
    await service.deactivate_school(school_id, requesting_user)
    return success_response(message="School deactivated.")
