"""
EduCore AI Platform — Custom Exception Hierarchy

Defines all application-specific exceptions. Each exception maps to
a specific HTTP status code and carries a machine-readable error code
for API consumers to programmatically handle failures.

Business Rule: All exceptions raised from services and repositories must
be subclasses of EduCoreException. Never raise raw HTTP exceptions from
the service layer.
"""

from typing import Any


class EduCoreException(Exception):
    """
    Base exception for the EduCore AI Platform.

    All custom exceptions must inherit from this class. Provides a
    consistent interface for the global exception handler.

    Attributes:
        message: Human-readable description of the error.
        code: Machine-readable error code for API consumers.
        status_code: HTTP status code to return.
        details: Optional additional context about the error.
    """

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# 400 Bad Request
# =============================================================================


class BadRequestException(EduCoreException):
    """Raised when the request is syntactically or semantically invalid."""

    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, details=details)


# =============================================================================
# 401 Unauthorized
# =============================================================================


class UnauthorizedException(EduCoreException):
    """Raised when the request lacks valid authentication credentials."""

    status_code = 401
    code = "UNAUTHORIZED"

    def __init__(
        self, message: str = "Authentication required", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, details=details)


class InvalidCredentialsException(UnauthorizedException):
    """Raised when email/password combination is invalid."""

    code = "INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__(message="Invalid email or password")


class TokenExpiredException(UnauthorizedException):
    """Raised when a JWT token has expired."""

    code = "TOKEN_EXPIRED"

    def __init__(self) -> None:
        super().__init__(message="Authentication token has expired")


class InvalidTokenException(UnauthorizedException):
    """Raised when a JWT token is malformed or invalid."""

    code = "INVALID_TOKEN"

    def __init__(self) -> None:
        super().__init__(message="Invalid authentication token")


# =============================================================================
# 403 Forbidden
# =============================================================================


class ForbiddenException(EduCoreException):
    """Raised when the authenticated user lacks permission for the action."""

    status_code = 403
    code = "FORBIDDEN"

    def __init__(
        self, message: str = "Access denied", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, details=details)


class InsufficientPermissionsException(ForbiddenException):
    """Raised when a user's role does not permit the requested action."""

    code = "INSUFFICIENT_PERMISSIONS"

    def __init__(self, required_role: str | None = None) -> None:
        message = "You do not have permission to perform this action"
        if required_role:
            message = f"This action requires the '{required_role}' role"
        super().__init__(message=message)


class SchoolAccessDeniedException(ForbiddenException):
    """Raised when a user attempts to access another school's data."""

    code = "SCHOOL_ACCESS_DENIED"

    def __init__(self) -> None:
        super().__init__(message="Access to this school's data is not permitted")


# =============================================================================
# 404 Not Found
# =============================================================================


class NotFoundException(EduCoreException):
    """
    Raised when a requested resource does not exist.

    Accepts either:
    - A full message string: NotFoundException("Student '123' not found.")
    - Named resource args: NotFoundException(resource="Student", resource_id="123")
    """

    status_code = 404
    code = "NOT_FOUND"

    def __init__(
        self,
        message: str | None = None,
        resource: str = "Resource",
        resource_id: str | None = None,
    ) -> None:
        if message is None:
            message = f"{resource} not found"
            if resource_id:
                message = f"{resource} with ID '{resource_id}' not found"
        super().__init__(message=message)


# Alias for clarity — used in auth contexts
AuthenticationException = UnauthorizedException


# =============================================================================
# 409 Conflict
# =============================================================================


class ConflictException(EduCoreException):
    """Raised when a request conflicts with the current state of the resource."""

    status_code = 409
    code = "CONFLICT"

    def __init__(
        self, message: str = "Resource already exists", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, details=details)


class DuplicateEmailException(ConflictException):
    """Raised when attempting to register an email that already exists."""

    code = "DUPLICATE_EMAIL"

    def __init__(self, email: str) -> None:
        super().__init__(message=f"An account with email '{email}' already exists")


class DuplicateEnrollmentException(ConflictException):
    """Raised when a student is already enrolled in the target class."""

    code = "DUPLICATE_ENROLLMENT"

    def __init__(self) -> None:
        super().__init__(message="Student is already enrolled in this class")


class DuplicateAttendanceException(ConflictException):
    """Raised when attendance is already recorded for a student on a given date."""

    code = "DUPLICATE_ATTENDANCE"

    def __init__(self) -> None:
        super().__init__(message="Attendance for this student on this date already exists")


# =============================================================================
# 422 Unprocessable Entity
# =============================================================================


class ValidationException(EduCoreException):
    """Raised when business rule validation fails."""

    status_code = 422
    code = "VALIDATION_ERROR"

    def __init__(
        self, message: str = "Validation failed", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, details=details)


class ClassCapacityExceededException(ValidationException):
    """Raised when enrolling a student would exceed class capacity."""

    code = "CLASS_CAPACITY_EXCEEDED"

    def __init__(self, message: str = "Class has reached maximum capacity", capacity: int | None = None) -> None:
        details = {"max_capacity": capacity} if capacity is not None else {}
        super().__init__(message=message, details=details)


class InvalidGradeException(ValidationException):
    """Raised when a grade value is invalid (negative or exceeds max)."""

    code = "INVALID_GRADE"

    def __init__(self, score: float, max_score: float) -> None:
        super().__init__(
            message=f"Score {score} is invalid. Must be between 0 and {max_score}",
            details={"score": score, "max_score": max_score},
        )


class AccountDeactivatedException(ValidationException):
    """Raised when an inactive user attempts to authenticate."""

    code = "ACCOUNT_DEACTIVATED"

    def __init__(self) -> None:
        super().__init__(message="This account has been deactivated")


class InactiveTeacherException(ValidationException):
    """Raised when assigning a class to an inactive teacher."""

    code = "INACTIVE_TEACHER"

    def __init__(self) -> None:
        super().__init__(message="Cannot assign class to an inactive teacher")
