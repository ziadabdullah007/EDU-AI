"""EduCore AI Platform — Attendance Schemas"""

from datetime import date
from uuid import UUID

from pydantic import Field

from app.models.attendance import AttendanceStatus
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class MarkAttendanceRequest(BaseSchema):
    """Request to mark attendance for a single student."""

    student_id: UUID = Field(description="Student to mark attendance for")
    class_id: UUID = Field(description="Class session")
    date: date = Field(description="Attendance date (YYYY-MM-DD)")
    status: AttendanceStatus = Field(description="Attendance status")
    notes: str | None = Field(default=None, max_length=500)


class BulkMarkAttendanceRequest(BaseSchema):
    """Request to mark attendance for multiple students at once."""

    class_id: UUID = Field(description="Class session")
    date: date = Field(description="Attendance date (YYYY-MM-DD)")
    records: list[dict] = Field(
        description="List of {student_id, status, notes} objects",
        min_length=1,
    )


class UpdateAttendanceRequest(BaseSchema):
    """Request to update an existing attendance record."""

    status: AttendanceStatus | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=500)


class AttendanceResponse(UUIDSchema, TimestampSchema):
    """Attendance record response."""

    student_id: UUID
    class_id: UUID
    school_id: UUID
    recorded_by: UUID
    date: date
    status: AttendanceStatus
    notes: str | None


class AttendanceSummaryResponse(BaseSchema):
    """Attendance statistics for a student or class."""

    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_rate: float = Field(description="Percentage of present days")
