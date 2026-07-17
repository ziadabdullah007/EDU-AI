"""
EduCore AI Platform — Test Configuration

Provides shared pytest fixtures for:
- Async test database sessions
- Test client
- Mock authenticated users with different roles
"""

import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.session import get_db_session
from app.main import app
from app.models.user import User, UserRole

# ── Test Database ──────────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for all async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test SQLite engine shared across the test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    import app.models  # noqa: F401 — register all models
    from app.database.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an AsyncClient with the test session injected.

    The database dependency is overridden to use the transactional test session.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ── Mock User Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_school_id() -> uuid4:
    return uuid4()


@pytest.fixture
def mock_super_admin(mock_school_id) -> User:
    """Return a mock SUPER_ADMIN user for testing."""
    return User(
        id=uuid4(),
        email="superadmin@educore.io",
        password_hash="$2b$12$hashed",
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        school_id=None,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def mock_school_admin(mock_school_id) -> User:
    """Return a mock SCHOOL_ADMIN user for testing."""
    return User(
        id=uuid4(),
        email="admin@school.com",
        password_hash="$2b$12$hashed",
        first_name="School",
        last_name="Admin",
        role=UserRole.SCHOOL_ADMIN,
        school_id=mock_school_id,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def mock_teacher(mock_school_id) -> User:
    """Return a mock TEACHER user for testing."""
    return User(
        id=uuid4(),
        email="teacher@school.com",
        password_hash="$2b$12$hashed",
        first_name="John",
        last_name="Teacher",
        role=UserRole.TEACHER,
        school_id=mock_school_id,
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def mock_student_user(mock_school_id) -> User:
    """Return a mock STUDENT user for testing."""
    return User(
        id=uuid4(),
        email="student@school.com",
        password_hash="$2b$12$hashed",
        first_name="Jane",
        last_name="Student",
        role=UserRole.STUDENT,
        school_id=mock_school_id,
        is_active=True,
        is_verified=True,
    )
