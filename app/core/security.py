"""
EduCore AI Platform — Security Utilities

Provides JWT token creation/validation and bcrypt password hashing.
This module is the single authority for all cryptographic operations.
It has no dependencies on FastAPI — it is pure Python and can be
tested without an HTTP context.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Password Utilities
# =============================================================================


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password string from the user.

    Returns:
        A bcrypt hash string safe to store in the database.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password: The raw password string provided by the user.
        hashed_password: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Utilities
# =============================================================================


def _create_token(
    subject: str,
    token_type: str,
    secret_key: str,
    expire_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Internal factory for creating signed JWT tokens.

    Args:
        subject: The token subject (typically user ID as string).
        token_type: Token type identifier ('access' or 'refresh').
        secret_key: The HMAC secret key for signing.
        expire_delta: How long until the token expires.
        additional_claims: Optional extra payload claims.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(UTC)
    expire = now + expire_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
    }

    if additional_claims:
        payload.update(additional_claims)

    settings = get_settings()
    return jwt.encode(payload, secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, role: str, school_id: UUID | None = None) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: The authenticated user's UUID.
        role: The user's role (e.g., 'SCHOOL_ADMIN', 'TEACHER').
        school_id: The school the user belongs to (None for SUPER_ADMIN).

    Returns:
        A signed JWT access token string.
    """
    settings = get_settings()
    claims: dict[str, Any] = {"role": role}
    if school_id is not None:
        claims["school_id"] = str(school_id)

    return _create_token(
        subject=str(user_id),
        token_type="access",
        secret_key=settings.jwt_secret_key,
        expire_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        additional_claims=claims,
    )


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a long-lived JWT refresh token.

    Args:
        user_id: The authenticated user's UUID.

    Returns:
        A signed JWT refresh token string.
    """
    settings = get_settings()
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        secret_key=settings.jwt_refresh_secret_key,
        expire_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

    if payload.get("type") != "access":
        raise JWTError("Token type mismatch: expected access token")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT refresh token.

    Args:
        token: The JWT refresh token string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    settings = get_settings()
    payload = jwt.decode(
        token, settings.jwt_refresh_secret_key, algorithms=[settings.jwt_algorithm]
    )

    if payload.get("type") != "refresh":
        raise JWTError("Token type mismatch: expected refresh token")

    return payload
