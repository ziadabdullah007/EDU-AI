"""
EduCore AI Platform — Application Entry Point

Bootstraps the FastAPI application, registers middleware, exception handlers,
event lifecycle hooks, and mounts all API routers.

Architecture:
    HTTP Request → Middleware → Router → Service → Repository → Database

This file is the single composition root of the application.
"""

from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import check_database_connection, dispose_engine
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown lifecycle.

    On startup:
        - Verify database connectivity.
        - Log application start.

    On shutdown:
        - Dispose SQLAlchemy connection pool.
        - Log application stop.
    """
    settings = get_settings()
    logger.info(
        "application_starting",
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

    db_ok = await check_database_connection()
    if not db_ok:
        logger.error("database_connection_failed_on_startup")
    else:
        logger.info("database_connection_verified")

    yield  # Application is running

    logger.info("application_shutting_down")
    await dispose_engine()
    logger.info("application_stopped")


def create_application() -> FastAPI:
    """
    Factory function that builds and configures the FastAPI application.

    Returns:
        A fully configured FastAPI instance ready to serve requests.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "EduCore AI Platform — Production-Ready Multi-School Backend API. "
            "Supports Authentication, Student Management, Teacher Management, "
            "Attendance, Grades, Payments, Documents, and more."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: applied bottom-up) ──────────────────────
    # SecurityHeadersMiddleware is innermost (applied last)
    app.add_middleware(SecurityHeadersMiddleware)

    # RequestLoggingMiddleware wraps security headers
    app.add_middleware(RequestLoggingMiddleware)

    # CORS is outermost — must be added after other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # ── Exception Handlers ─────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── API Routers ────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Health Check ───────────────────────────────────────────────────────
    @app.get(
        "/health",
        tags=["Health"],
        summary="Platform health check",
        description="Returns application version, uptime status, and database connectivity.",
    )
    async def health_check() -> dict:
        db_healthy = await check_database_connection()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "database": "connected" if db_healthy else "unreachable",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    return app


# ── Application instance ───────────────────────────────────────────────────
# Exported for Uvicorn: `uvicorn app.main:app`
app = create_application()
