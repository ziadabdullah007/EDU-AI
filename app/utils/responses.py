"""
EduCore AI Platform — API Response Builders

Provides factory functions for building consistent API response envelopes.
Every endpoint should use these builders instead of returning raw data.

Standard envelopes:
    Success:  {"success": true,  "message": "...", "data": {...}}
    Failure:  {"success": false, "message": "...", "errors": [...]}
    Paginated: {"success": true, "message": "...", "data": {...}, "pagination": {...}}
"""

from typing import Any


def success_response(
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    """
    Build a standard success response envelope.

    Args:
        message: Human-readable success message.
        data: The response payload (model, dict, or None).

    Returns:
        A dictionary matching the standard success envelope.
    """
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def paginated_response(
    message: str,
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    total_pages: int,
    has_next: bool,
    has_prev: bool,
) -> dict[str, Any]:
    """
    Build a standard paginated list response envelope.

    Args:
        message: Human-readable success message.
        items: The records for the current page.
        total: Total number of records.
        page: Current page number.
        page_size: Records per page.
        total_pages: Total pages available.
        has_next: Whether a next page exists.
        has_prev: Whether a previous page exists.

    Returns:
        A dictionary with items and pagination metadata.
    """
    return {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        },
    }
