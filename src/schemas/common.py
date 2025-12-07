"""
Common schemas for pagination, filtering, and standard responses.
"""

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class OrderDirection(str, Enum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    order_by: str | None = Field(None, description="Field to order by")
    order_direction: OrderDirection = Field(OrderDirection.DESC, description="Order direction")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    message: str
    error_code: str | None = None
    details: dict[str, Any] | None = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
    timestamp: str


class AllHealthCheckResponse(HealthCheckResponse):
    database: bool = False
    redis: bool = False


class StatsResponse(BaseModel):
    """Generic statistics response."""

    period: str
    data: dict[str, Any]
    generated_at: str
