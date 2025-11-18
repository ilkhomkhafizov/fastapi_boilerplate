"""
Schemas module containing all Pydantic models for validation.
"""

from src.schemas.auth import (
    EmailVerificationRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
    TokenData,
)
from src.schemas.common import (
    ErrorResponse,
    HealthCheckResponse,
    OrderDirection,
    PaginatedResponse,
    PaginationParams,
    StatsResponse,
    SuccessResponse,
)
from src.schemas.post import (
    PostBase,
    PostCreate,
    PostList,
    PostResponse,
    PostStats,
    PostUpdate,
)
from src.schemas.user import (
    UserAdminUpdate,
    UserBase,
    UserCreate,
    UserList,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
    UserWithStats,
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
