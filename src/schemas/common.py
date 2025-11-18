"""
Common schemas for pagination, filtering, and standard responses.
"""

from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


T = TypeVar("T")


class OrderDirection(str, Enum):
    """Order direction for sorting."""
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    order_by: Optional[str] = Field(None, description="Field to order by")
    order_direction: OrderDirection = Field(OrderDirection.DESC, description="Order direction")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    items: List[T]
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
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str
    environment: str
    database: bool = False
    redis: bool = False
    timestamp: str


class StatsResponse(BaseModel):
    """Generic statistics response."""
    
    period: str
    data: Dict[str, Any]
    generated_at: str
