"""EduCore AI Platform — Models Package

Imports all ORM models to ensure SQLAlchemy registers them
in the metadata before Alembic or any migration tool runs.
"""

from app.models.attendance import Attendance, AttendanceStatus
from app.models.base import SoftDeleteMixin, TimestampMixin
from app.models.class_ import Class
from app.models.document import Document, DocumentCategory
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import AssessmentType, Grade
from app.models.payment import Payment, PaymentStatus, PaymentType
from app.models.refresh_token import RefreshToken
from app.models.school import School
from app.models.student import Gender, Student
from app.models.teacher import Teacher
from app.models.user import User, UserRole

__all__ = [
    # Base mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    # Models
    "School",
    "User",
    "UserRole",
    "RefreshToken",
    "Student",
    "Gender",
    "Teacher",
    "Class",
    "Enrollment",
    "EnrollmentStatus",
    "Attendance",
    "AttendanceStatus",
    "Grade",
    "AssessmentType",
    "Payment",
    "PaymentType",
    "PaymentStatus",
    "Document",
    "DocumentCategory",
]
