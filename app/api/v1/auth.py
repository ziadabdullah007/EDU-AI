"""
EduCore AI Platform — Authentication Router

All routes delegate to AuthService. No business logic here.
"""

from fastapi import APIRouter, Depends, status

from app.dependencies import (
    get_auth_service,
    get_current_user,
    require_school_admin,
)
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService
from app.utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. SUPER_ADMIN role cannot be self-registered.",
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    user = await service.register(payload)
    return success_response(data=user.model_dump(), message="User registered successfully.")


@router.post(
    "/login",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Validate credentials and return JWT access + refresh tokens.",
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    tokens = await service.login(payload)
    return success_response(data=tokens.model_dump(), message="Login successful.")


@router.post(
    "/refresh",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    new_token = await service.refresh_access_token(payload)
    return success_response(data=new_token.model_dump(), message="Token refreshed.")


@router.post(
    "/logout",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revoke all refresh tokens for the current user.",
)
async def logout(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    await service.logout(current_user)
    return success_response(message="Logged out from all devices successfully.")


@router.get(
    "/me",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Return the authenticated user's public profile.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    profile = UserResponse.model_validate(current_user)
    return success_response(data=profile.model_dump(), message="Profile retrieved.")


@router.post(
    "/change-password",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the current user's password. Invalidates all active sessions.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    await service.change_password(current_user, payload)
    return success_response(message="Password changed successfully.")


@router.patch(
    "/deactivate/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user account",
    description="Deactivate a user account. Requires SCHOOL_ADMIN or SUPER_ADMIN role.",
)
async def deactivate_account(
    user_id: str,
    requesting_user: User = Depends(require_school_admin),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    from uuid import UUID
    await service.deactivate_account(UUID(user_id), requesting_user)
    return success_response(message="Account deactivated successfully.")
