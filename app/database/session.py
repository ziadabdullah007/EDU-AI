"""
EduCore AI Platform — Database Session Management

Configures the async SQLAlchemy engine and session factory.
The session is injected via FastAPI Depends — never instantiated manually.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Return the singleton async SQLAlchemy engine.

    The engine is created once and reused throughout the application
    lifecycle. Connection pool settings come from application config.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,   # Validates connections before use
            echo=settings.debug,  # SQL logging in debug mode only
        )
        logger.info("Database engine initialized", pool_size=settings.database_pool_size)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return the singleton async session factory.

    Sessions produced by this factory are scoped to individual requests
    and automatically rolled back on failure.
    """
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.

    Yields a single async session and ensures it is closed after
    the request completes, regardless of success or failure.

    Usage:
        async def my_endpoint(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """
    Verify the database connection is healthy.

    Used by the health check endpoint to report database status.

    Returns:
        True if the database is reachable, False otherwise.
    """
    from sqlalchemy import text

    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        return False


async def dispose_engine() -> None:
    """
    Dispose the database engine and close all connections.

    Called during application shutdown to cleanly release resources.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
        _engine = None
