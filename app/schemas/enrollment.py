"""EduCore AI Platform — Enrollment Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enrollment import EnrollmentStatus
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class EnrollStudentRequest(BaseSchema):
    """Request to enroll a student in a class."""

    student_id: UUID = Field(description="Student to enroll")
    class_id: UUID = Field(description="Target class")
    notes: str | None = Field(default=None, max_length=500, description="Enrollment notes")


class TransferStudentRequest(BaseSchema):
    """Request to transfer a student from their current class to another."""

    student_id: UUID = Field(description="Student to transfer")
    target_class_id: UUID = Field(description="Class to transfer the student into")
    notes: str | None = Field(default=None, max_length=500, description="Transfer reason")


class EnrollmentResponse(UUIDSchema, TimestampSchema):
    """Enrollment record response."""

    student_id: UUID
    class_id: UUID
    school_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    withdrawn_at: datetime | None
    notes: str | None
