"""EduCore AI Platform — Services Package"""

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

__all__ = [
    "AttendanceService",
    "AuthService",
    "ClassService",
    "DocumentService",
    "EnrollmentService",
    "GradeService",
    "PaymentService",
    "SchoolService",
    "StudentService",
    "TeacherService",
]
