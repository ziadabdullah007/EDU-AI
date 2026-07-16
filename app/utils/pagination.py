"""
EduCore AI Platform — Pagination Utilities

Provides consistent pagination logic used across all list endpoints.
All list endpoints must support page/page_size parameters and return
a standardized paginated response envelope.
"""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")

# Business constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1


class PaginationParams(BaseModel):
    """
    Standard query parameters for paginated endpoints.

    Injected via FastAPI Depends to ensure consistent validation
    across all list endpoints.

    Attributes:
        page: 1-indexed page number.
        page_size: Number of records per page (max 100).
        search: Optional full-text search query.
        sort_by: Field name to sort by.
        sort_order: Sort direction ('asc' or 'desc').
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description="Number of records per page",
    )
    search: str | None = Field(default=None, description="Full-text search query")
    sort_by: str = Field(default="created_at", description="Field name to sort by")
    sort_order: str = Field(default="desc", description="Sort direction: asc or desc")

    @field_validator("sort_order", mode="before")
    @classmethod
    def normalize_sort_order(cls, v: str) -> str:
        """Normalize sort_order to lowercase."""
        return v.lower() if v else "desc"

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Ensure sort_order is 'asc' or 'desc'."""
        if v not in ("asc", "desc"):
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET from page and page_size."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Alias for page_size used in SQL LIMIT clauses."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response envelope for list endpoints.

    Attributes:
        items: The list of items for the current page.
        total: Total number of records across all pages.
        page: Current page number.
        page_size: Number of records per page.
        total_pages: Total number of pages.
        has_next: Whether a next page exists.
        has_prev: Whether a previous page exists.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def build_paginated_response(
    items: list[T],
    total: int,
    params: PaginationParams,
) -> PaginatedResponse[T]:
    """
    Build a standardized paginated response from a list of items.

    Args:
        items: The records for the current page.
        total: Total count of records across all pages.
        params: The pagination parameters from the request.

    Returns:
        A fully populated PaginatedResponse instance.
    """
    total_pages = max(1, math.ceil(total / params.page_size))
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )
