"""
EduCore AI Platform — Authentication Schemas

Request and response schemas for all authentication endpoints.
Passwords are never returned in any response schema.
"""

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema

# =============================================================================
# Request Schemas
# =============================================================================


class RegisterRequest(BaseSchema):
    """
    Schema for new user registration.

    Business Rule: Email must be unique platform-wide.
    """

    email: EmailStr = Field(description="User's email address (must be unique)")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)",
    )
    first_name: str = Field(min_length=1, max_length=100, description="First name")
    last_name: str = Field(min_length=1, max_length=100, description="Last name")
    role: UserRole = Field(description="User role on the platform")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce basic password complexity rules."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseSchema):
    """Credentials for user login."""

    email: EmailStr = Field(description="Registered email address")
    password: str = Field(description="Account password")


class RefreshTokenRequest(BaseSchema):
    """Refresh token payload for token rotation."""

    refresh_token: str = Field(description="A valid, non-revoked refresh token")


class ChangePasswordRequest(BaseSchema):
    """Request schema for authenticated password change."""

    current_password: str = Field(description="Current account password")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Enforce password complexity on the new password."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class ResetPasswordRequest(BaseSchema):
    """Request to reset a user's password (admin action)."""

    user_id: str = Field(description="UUID of the user whose password will be reset")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password for the user",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class UserResponse(UUIDSchema, TimestampSchema):
    """
    Public user profile.

    IMPORTANT: Never include password_hash in this schema.
    """

    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool


class TokenResponse(BaseSchema):
    """Response containing access and refresh tokens after authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class AccessTokenResponse(BaseSchema):
    """Response containing only a new access token (from refresh)."""

    access_token: str
    token_type: str = "bearer"
