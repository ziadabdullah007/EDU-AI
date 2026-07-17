"""
EduCore AI Platform — FastAPI Dependency Providers

Provides injectable dependencies for database sessions, repositories,
services, and the currently authenticated user.

All dependencies follow FastAPI's Depends injection pattern.
Never instantiate repositories or services directly inside routers.
"""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.database.session import get_db_session
from app.exceptions.errors import (
    AuthenticationException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User, UserRole
from app.repositories.attendance import AttendanceRepository
from app.repositories.class_ import ClassRepository
from app.repositories.document import DocumentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.grade import GradeRepository
from app.repositories.payment import PaymentRepository
from app.repositories.school import SchoolRepository
from app.repositories.student import StudentRepository
from app.repositories.teacher import TeacherRepository
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.services.attendance import AttendanceService
from app.services.auth import AuthService
from app.services.class_ import ClassService
from app.services.document import DocumentService
from app.services.enrollment import EnrollmentService
from app.services.grade import GradeService
from app.services.payment import PaymentService
from app.services.school import SchoolService
from app.services.student import StudentService
from app.services.teacher import TeacherService

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# HTTP Bearer scheme — used to extract the JWT from the Authorization header.
# auto_error=False lets us raise a custom 401 instead of FastAPI's default.
# ─────────────────────────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# Repository Providers
# =============================================================================


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Provide a UserRepository bound to the current request session."""
    return UserRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshTokenRepository:
    """Provide a RefreshTokenRepository bound to the current request session."""
    return RefreshTokenRepository(session)


def get_school_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SchoolRepository:
    """Provide a SchoolRepository bound to the current request session."""
    return SchoolRepository(session)


def get_student_repository(
    session: AsyncSession = Depends(get_db_session),
) -> StudentRepository:
    """Provide a StudentRepository bound to the current request session."""
    return StudentRepository(session)


def get_teacher_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TeacherRepository:
    """Provide a TeacherRepository bound to the current request session."""
    return TeacherRepository(session)


def get_class_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ClassRepository:
    """Provide a ClassRepository bound to the current request session."""
    return ClassRepository(session)


def get_enrollment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EnrollmentRepository:
    """Provide an EnrollmentRepository bound to the current request session."""
    return EnrollmentRepository(session)


def get_attendance_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AttendanceRepository:
    """Provide an AttendanceRepository bound to the current request session."""
    return AttendanceRepository(session)


def get_grade_repository(
    session: AsyncSession = Depends(get_db_session),
) -> GradeRepository:
    """Provide a GradeRepository bound to the current request session."""
    return GradeRepository(session)


def get_payment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PaymentRepository:
    """Provide a PaymentRepository bound to the current request session."""
    return PaymentRepository(session)


def get_document_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepository:
    """Provide a DocumentRepository bound to the current request session."""
    return DocumentRepository(session)


# =============================================================================
# Service Providers
# =============================================================================


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    """Provide an AuthService with its required repositories."""
    return AuthService(user_repo=user_repo, token_repo=token_repo)


def get_school_service(
    school_repo: SchoolRepository = Depends(get_school_repository),
) -> SchoolService:
    """Provide a SchoolService with its required repositories."""
    return SchoolService(school_repo=school_repo)


def get_student_service(
    student_repo: StudentRepository = Depends(get_student_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> StudentService:
    """Provide a StudentService with its required repositories."""
    return StudentService(student_repo=student_repo, user_repo=user_repo)


def get_teacher_service(
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> TeacherService:
    """Provide a TeacherService with its required repositories."""
    return TeacherService(teacher_repo=teacher_repo, user_repo=user_repo)


def get_class_service(
    class_repo: ClassRepository = Depends(get_class_repository),
    teacher_repo: TeacherRepository = Depends(get_teacher_repository),
) -> ClassService:
    """Provide a ClassService with its required repositories."""
    return ClassService(class_repo=class_repo, teacher_repo=teacher_repo)


def get_enrollment_service(
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    class_repo: ClassRepository = Depends(get_class_repository),
    student_repo: StudentRepository = Depends(get_student_repository),
) -> EnrollmentService:
    """Provide an EnrollmentService with its required repositories."""
    return EnrollmentService(
        enrollment_repo=enrollment_repo,
        class_repo=class_repo,
        student_repo=student_repo,
    )


def get_attendance_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    class_repo: ClassRepository = Depends(get_class_repository),
) -> AttendanceService:
    """Provide an AttendanceService with its required repositories."""
    return AttendanceService(
        attendance_repo=attendance_repo,
        enrollment_repo=enrollment_repo,
        class_repo=class_repo,
    )


def get_grade_service(
    grade_repo: GradeRepository = Depends(get_grade_repository),
    enrollment_repo: EnrollmentRepository = Depends(get_enrollment_repository),
    class_repo: ClassRepository = Depends(get_class_repository),
) -> GradeService:
    """Provide a GradeService with its required repositories."""
    return GradeService(
        grade_repo=grade_repo,
        enrollment_repo=enrollment_repo,
        class_repo=class_repo,
    )


def get_payment_service(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    student_repo: StudentRepository = Depends(get_student_repository),
) -> PaymentService:
    """Provide a PaymentService with its required repositories."""
    return PaymentService(payment_repo=payment_repo, student_repo=student_repo)


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentService:
    """Provide a DocumentService with its required repository."""
    return DocumentService(document_repo=document_repo)


# =============================================================================
# Authentication & Authorization Dependencies
# =============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Decode the JWT access token and return the active User.

    This dependency is the primary authentication gate. Every protected
    endpoint should declare it via Depends.

    Raises:
        AuthenticationException: If the token is missing, invalid, or expired.
        NotFoundException: If the user referenced in the token no longer exists.
        ForbiddenException: If the user account is deactivated.
    """
    if credentials is None:
        raise AuthenticationException("Authorization header is required")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise AuthenticationException("Invalid or expired access token") from exc

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Token payload is malformed: missing subject")

    try:
        user_id = UUID(user_id_str)
    except ValueError as exc:
        raise AuthenticationException("Token payload contains an invalid user ID") from exc

    user = await user_repo.get_active_by_id(user_id)
    if user is None:
        raise NotFoundException("Authenticated user not found or account deactivated")

    return user


def require_roles(*roles: UserRole):
    """
    Factory that returns a dependency enforcing one of the given roles.

    Usage in a router::

        @router.get("/admin-only")
        async def admin_endpoint(
            _: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN))
        ):
            ...

    Args:
        *roles: One or more UserRole values that are permitted.

    Returns:
        A FastAPI dependency function that returns the current user
        if they have an allowed role, or raises ForbiddenException.
    """

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user

    return _check


# ─────────────────────────────────────────────────────────────────────────────
# Convenience role shortcuts
# ─────────────────────────────────────────────────────────────────────────────

require_super_admin = require_roles(UserRole.SUPER_ADMIN)
require_school_admin = require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
require_teacher = require_roles(UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
require_student = require_roles(
    UserRole.STUDENT, UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN
)
