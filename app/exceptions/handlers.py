"""
EduCore AI Platform — Global Exception Handlers

Registers FastAPI exception handlers that convert exceptions into
consistent JSON responses. This is the single place where exceptions
are translated into HTTP responses.

All handlers follow the standard response envelope:
    {
        "success": false,
        "message": "...",
        "errors": []
    }
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.exceptions.errors import EduCoreException

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    message: str,
    code: str = "ERROR",
    errors: list[dict] | None = None,
) -> JSONResponse:
    """
    Build a consistent error JSON response.

    Args:
        status_code: HTTP status code.
        message: Human-readable error summary.
        code: Machine-readable error code.
        errors: Optional list of field-level validation errors.

    Returns:
        A FastAPI JSONResponse with the standard error envelope.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "code": code,
            "errors": errors or [],
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance to attach handlers to.
    """

    @app.exception_handler(EduCoreException)
    async def handle_edu_core_exception(
        request: Request, exc: EduCoreException
    ) -> JSONResponse:
        """Handle all custom application exceptions."""
        logger.warning(
            "Application exception",
            code=exc.code,
            message=exc.message,
            path=str(request.url.path),
            method=request.method,
        )
        return _error_response(
            status_code=exc.status_code,
            message=exc.message,
            code=exc.code,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic request validation failures."""
        errors = [
            {
                "field": " -> ".join(str(loc) for loc in error["loc"] if loc != "body"),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        logger.info(
            "Request validation failed",
            path=str(request.url.path),
            error_count=len(errors),
        )
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            code="VALIDATION_ERROR",
            errors=errors,
        )

    @app.exception_handler(JWTError)
    async def handle_jwt_error(request: Request, exc: JWTError) -> JSONResponse:
        """Handle JWT decode/validation failures."""
        logger.warning(
            "JWT validation failed",
            path=str(request.url.path),
            error=str(exc),
        )
        return _error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid or expired authentication token",
            code="INVALID_TOKEN",
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle unexpected database errors without exposing internals."""
        logger.error(
            "Database error",
            path=str(request.url.path),
            error=str(exc),
            exc_info=True,
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="A database error occurred. Please try again later.",
            code="DATABASE_ERROR",
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler for unhandled exceptions."""
        logger.error(
            "Unhandled exception",
            path=str(request.url.path),
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An internal server error occurred. Please try again later.",
            code="INTERNAL_ERROR",
        )
