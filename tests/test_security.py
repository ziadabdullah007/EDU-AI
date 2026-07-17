"""
EduCore AI Platform — Security Service Unit Tests

Tests the security module (JWT + bcrypt) in isolation.
These tests have no database or HTTP dependency.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests for bcrypt password hashing utilities."""

    def test_hash_password_returns_string(self) -> None:
        """hash_password should return a non-empty string."""
        result = hash_password("mysecretpassword1")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_is_not_plain_text(self) -> None:
        """Hash must not equal the plain-text password."""
        plain = "mysecretpassword1"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_correct_password(self) -> None:
        """verify_password should return True for a matching password."""
        plain = "correctpassword1"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self) -> None:
        """verify_password should return False for a non-matching password."""
        hashed = hash_password("correctpassword1")
        assert verify_password("wrongpassword1", hashed) is False

    def test_same_password_produces_different_hashes(self) -> None:
        """bcrypt should produce different hashes for the same input (salted)."""
        plain = "samepassword1"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2


class TestJWTTokens:
    """Tests for JWT access and refresh token creation/validation."""

    def test_create_and_decode_access_token(self) -> None:
        """A created access token should decode correctly."""
        user_id = uuid4()
        token = create_access_token(user_id=user_id, role="SCHOOL_ADMIN")
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "SCHOOL_ADMIN"
        assert payload["type"] == "access"

    def test_access_token_contains_school_id(self) -> None:
        """Access token should embed school_id when provided."""
        user_id = uuid4()
        school_id = uuid4()
        token = create_access_token(user_id=user_id, role="TEACHER", school_id=school_id)
        payload = decode_access_token(token)
        assert payload["school_id"] == str(school_id)

    def test_create_and_decode_refresh_token(self) -> None:
        """A created refresh token should decode correctly."""
        user_id = uuid4()
        token = create_refresh_token(user_id=user_id)
        payload = decode_refresh_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_access_token_wrong_type_raises(self) -> None:
        """Decoding a refresh token as access token should raise JWTError."""
        user_id = uuid4()
        refresh_token = create_refresh_token(user_id=user_id)
        with pytest.raises(JWTError):
            decode_access_token(refresh_token)

    def test_refresh_token_wrong_type_raises(self) -> None:
        """Decoding an access token as refresh token should raise JWTError."""
        user_id = uuid4()
        access_token = create_access_token(user_id=user_id, role="TEACHER")
        with pytest.raises(JWTError):
            decode_refresh_token(access_token)

    def test_tampered_token_raises(self) -> None:
        """Modifying a token should cause JWTError on decode."""
        user_id = uuid4()
        token = create_access_token(user_id=user_id, role="STUDENT")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_access_token(tampered)
