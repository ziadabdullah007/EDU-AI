"""EduCore AI Platform — Schemas Package"""

from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceSummaryResponse,
    BulkMarkAttendanceRequest,
    MarkAttendanceRequest,
    UpdateAttendanceRequest,
)
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.schemas.class_ import (
    AssignTeacherRequest,
    ClassCreateRequest,
    ClassResponse,
    ClassUpdateRequest,
    ClassWithEnrollmentCountResponse,
)
from app.schemas.document import DocumentCreateRequest, DocumentResponse, DocumentUpdateRequest
from app.schemas.enrollment import (
    EnrollmentResponse,
    EnrollStudentRequest,
    TransferStudentRequest,
)
from app.schemas.grade import (
    AddGradeRequest,
    GradeResponse,
    GradeStatisticsResponse,
    UpdateGradeRequest,
)
from app.schemas.payment import (
    CreatePaymentRequest,
    PaymentResponse,
    StudentBalanceResponse,
    UpdatePaymentRequest,
)
from app.schemas.school import SchoolCreateRequest, SchoolResponse, SchoolUpdateRequest
from app.schemas.student import StudentCreateRequest, StudentResponse, StudentUpdateRequest
from app.schemas.teacher import TeacherCreateRequest, TeacherResponse, TeacherUpdateRequest

__all__ = [
    "AssignTeacherRequest",
    "BaseSchema",
    "TimestampSchema",
    "UUIDSchema",
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "TokenResponse",
    "AccessTokenResponse",
    "UserResponse",
    "SchoolCreateRequest",
    "SchoolUpdateRequest",
    "SchoolResponse",
    "StudentCreateRequest",
    "StudentUpdateRequest",
    "StudentResponse",
    "TeacherCreateRequest",
    "TeacherUpdateRequest",
    "TeacherResponse",
    "ClassCreateRequest",
    "ClassUpdateRequest",
    "ClassResponse",
    "ClassWithEnrollmentCountResponse",
    "EnrollStudentRequest",
    "TransferStudentRequest",
    "EnrollmentResponse",
    "MarkAttendanceRequest",
    "BulkMarkAttendanceRequest",
    "UpdateAttendanceRequest",
    "AttendanceResponse",
    "AttendanceSummaryResponse",
    "AddGradeRequest",
    "UpdateGradeRequest",
    "GradeResponse",
    "GradeStatisticsResponse",
    "CreatePaymentRequest",
    "UpdatePaymentRequest",
    "PaymentResponse",
    "StudentBalanceResponse",
    "DocumentCreateRequest",
    "DocumentUpdateRequest",
    "DocumentResponse",
]
