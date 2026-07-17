"""
EduCore AI Platform — Authentication API Tests

Tests for registration, login, token refresh, and logout endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """The /health endpoint should return 200 with status information."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """A valid registration request should create a user and return 201."""
    payload = {
        "email": "newuser@test.com",
        "password": "SecurePass1",
        "first_name": "Test",
        "last_name": "User",
        "role": "SCHOOL_ADMIN",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Registering with an already-used email should return 409."""
    payload = {
        "email": "duplicate@test.com",
        "password": "SecurePass1",
        "first_name": "First",
        "last_name": "User",
        "role": "SCHOOL_ADMIN",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_super_admin_forbidden(client: AsyncClient) -> None:
    """Self-registering as SUPER_ADMIN must be rejected with 403."""
    payload = {
        "email": "superadmin@test.com",
        "password": "SecurePass1",
        "first_name": "Super",
        "last_name": "Admin",
        "role": "SUPER_ADMIN",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Valid credentials should return access and refresh tokens."""
    await client.post("/api/v1/auth/register", json={
        "email": "logintest@test.com",
        "password": "SecurePass1",
        "first_name": "Login",
        "last_name": "Test",
        "role": "SCHOOL_ADMIN",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "logintest@test.com",
        "password": "SecurePass1",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Wrong password should return 401."""
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpass@test.com",
        "password": "SecurePass1",
        "first_name": "Wrong",
        "last_name": "Pass",
        "role": "SCHOOL_ADMIN",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "WrongPassword1",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    """Accessing /me without a token should return 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient) -> None:
    """Accessing /me with a valid token should return user profile."""
    # Register and login
    await client.post("/api/v1/auth/register", json={
        "email": "metest@test.com",
        "password": "SecurePass1",
        "first_name": "Me",
        "last_name": "Test",
        "role": "SCHOOL_ADMIN",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "metest@test.com",
        "password": "SecurePass1",
    })
    token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "metest@test.com"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    """Passwords without digits or letters should be rejected with 422."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "weak@test.com",
        "password": "onlyletters",
        "first_name": "Weak",
        "last_name": "Pass",
        "role": "SCHOOL_ADMIN",
    })
    assert response.status_code == 422
