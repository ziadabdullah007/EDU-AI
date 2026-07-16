"""
EduCore AI Platform — Shared Validators

Reusable validation functions for common fields like phone numbers,
student numbers, and Egyptian-specific formats. These are pure functions
with no side effects — safe to call from any layer.
"""

import re
from datetime import date


# Egyptian phone number pattern (starts with 01 followed by 9 digits)
_EGYPTIAN_PHONE_PATTERN = re.compile(r"^01[0125]\d{8}$")

# International phone: +country_code followed by 7-15 digits
_INTERNATIONAL_PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{6,14}$")

# Student/Employee number: alphanumeric with optional hyphens
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{3,30}$")


def validate_phone_number(phone: str) -> str:
    """
    Validate and normalize a phone number.

    Accepts Egyptian mobile numbers (01XXXXXXXXX) and international
    formats. Strips whitespace before validation.

    Args:
        phone: Raw phone number string.

    Returns:
        The cleaned phone number string.

    Raises:
        ValueError: If the phone number format is invalid.
    """
    cleaned = phone.strip().replace(" ", "").replace("-", "")

    if _EGYPTIAN_PHONE_PATTERN.match(cleaned):
        return cleaned

    if _INTERNATIONAL_PHONE_PATTERN.match(cleaned):
        return cleaned

    raise ValueError(
        f"Invalid phone number: '{phone}'. "
        "Accepted formats: Egyptian (01XXXXXXXXX) or international (+XXXXXXXXXXX)"
    )


def validate_student_number(student_number: str) -> str:
    """
    Validate a student identifier number.

    Student numbers must be 3-30 characters, containing only
    alphanumeric characters, hyphens, or underscores.

    Args:
        student_number: The student ID string.

    Returns:
        The cleaned student number.

    Raises:
        ValueError: If the format is invalid.
    """
    cleaned = student_number.strip().upper()

    if not _IDENTIFIER_PATTERN.match(cleaned):
        raise ValueError(
            f"Invalid student number: '{student_number}'. "
            "Must be 3-30 alphanumeric characters (hyphens and underscores allowed)"
        )

    return cleaned


def validate_birth_date(birth_date: date) -> date:
    """
    Validate that a birth date is reasonable.

    Rejects dates in the future and dates more than 120 years ago.

    Args:
        birth_date: The birth date to validate.

    Returns:
        The validated birth date.

    Raises:
        ValueError: If the date is unreasonable.
    """
    today = date.today()

    if birth_date > today:
        raise ValueError("Birth date cannot be in the future")

    age_years = (today - birth_date).days / 365.25
    if age_years > 120:
        raise ValueError("Birth date is too far in the past")

    return birth_date


def validate_employee_number(employee_number: str) -> str:
    """
    Validate a teacher/employee identifier number.

    Args:
        employee_number: The employee ID string.

    Returns:
        The cleaned employee number.

    Raises:
        ValueError: If the format is invalid.
    """
    cleaned = employee_number.strip().upper()

    if not _IDENTIFIER_PATTERN.match(cleaned):
        raise ValueError(
            f"Invalid employee number: '{employee_number}'. "
            "Must be 3-30 alphanumeric characters"
        )

    return cleaned
