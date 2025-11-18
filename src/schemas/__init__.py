"""
Schemas module containing all Pydantic models for validation.
"""

from src.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
    UserResponse,
    UserWithStats,
    UserList,
    UserAdminUpdate,
)
from src.schemas.post import (
    PostBase,
    PostCreate,
    PostUpdate,
    PostResponse,
    PostList,
    PostStats,
)
from src.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
)
from src.schemas.common import (
    OrderDirection,
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    HealthCheckResponse,
    StatsResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserUpdatePassword",
    "UserResponse",
    "UserWithStats",
    "UserList",
    "UserAdminUpdate",
    # Post schemas
    "PostBase",
    "PostCreate",
    "PostUpdate",
    "PostResponse",
    "PostList",
    "PostStats",
    # Auth schemas
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "EmailVerificationRequest",
    # Common schemas
    "OrderDirection",
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "StatsResponse",
]
