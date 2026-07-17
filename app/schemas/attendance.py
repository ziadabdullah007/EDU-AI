"""
EduCore AI Platform — Attendance Schemas

Request and response schemas for attendance tracking.
"""

from datetime import date
from uuid import UUID

from pydantic import Field

from app.models.attendance import AttendanceStatus
from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class AttendanceEntryRecord(BaseSchema):
    """A single attendance entry for bulk marking."""

    student_id: UUID
    status: AttendanceStatus
    notes: str | None = Field(default=None, max_length=500)


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
    records: list[AttendanceEntryRecord] = Field(
        description="List of student attendance entries",
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
    recorded_by: UUID
    date: date
    status: AttendanceStatus
    notes: str | None


class AttendanceSummaryResponse(BaseSchema):
    """Attendance statistics for a student within a date range."""

    student_id: UUID
    total_days: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_rate: float = Field(description="Percentage of present days (0-100)")
