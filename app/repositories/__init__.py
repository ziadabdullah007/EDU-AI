"""EduCore AI Platform — Repositories Package"""

from app.repositories.attendance import AttendanceRepository
from app.repositories.base import BaseRepository
from app.repositories.class_ import ClassRepository
from app.repositories.document import DocumentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.grade import GradeRepository
from app.repositories.payment import PaymentRepository
from app.repositories.school import SchoolRepository
from app.repositories.student import StudentRepository
from app.repositories.teacher import TeacherRepository
from app.repositories.user import RefreshTokenRepository, UserRepository

__all__ = [
    "AttendanceRepository",
    "BaseRepository",
    "ClassRepository",
    "DocumentRepository",
    "EnrollmentRepository",
    "GradeRepository",
    "PaymentRepository",
    "RefreshTokenRepository",
    "SchoolRepository",
    "StudentRepository",
    "TeacherRepository",
    "UserRepository",
]
