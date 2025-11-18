"""
Users API routes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import (
    get_current_admin_user,
    get_current_super_admin_user,
    get_current_user,
)
from src.api.dependencies.pagination import calculate_offset, calculate_pages, get_pagination_params
from src.core.database import get_db
from src.core.logging import get_logger
from src.core.security import security_manager
from src.models.user import User, UserRole
from src.repositories.post import PostRepository
from src.repositories.user import UserRepository
from src.schemas.common import PaginationParams, SuccessResponse
from src.schemas.post import PostList
from src.schemas.user import (
    UserAdminUpdate,
    UserList,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
    UserWithStats,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserList)
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_active: bool | None = Query(None, description="Filter by active status"),
    role: UserRole | None = Query(None, description="Filter by role"),
    search: str | None = Query(None, description="Search in email, username, and name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> UserList:
    """
    List all users (admin only).

    Args:
        pagination: Pagination parameters
        is_active: Filter by active status
        role: Filter by role
        search: Search query
        db: Database session
        current_user: Current admin user

    Returns:
        UserList: Paginated list of users
    """
    user_repo = UserRepository(db)

    offset = calculate_offset(pagination.page, pagination.page_size)

    users, total = await user_repo.list_users(
        skip=offset,
        limit=pagination.page_size,
        is_active=is_active,
        role=role,
        search=search,
    )

    return UserList(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=calculate_pages(total, pagination.page_size),
    )


@router.get("/me", response_model=UserWithStats)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserWithStats:
    """
    Get current user profile with statistics.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserWithStats: User profile with stats
    """
    post_repo = PostRepository(db)
    stats = await post_repo.get_post_stats(user_id=current_user.id)

    user_dict = UserResponse.model_validate(current_user).model_dump()

    return UserWithStats(
        **user_dict,
        post_count=stats["total_posts"],
        total_views=stats["total_views"],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get user by ID (public profile).

    Args:
        user_id: User ID
        db: Database session

    Returns:
        UserResponse: User profile

    Raises:
        HTTPException: If user not found
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Update current user profile.

    Args:
        user_update: Update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Updated user profile
    """
    user_repo = UserRepository(db)

    # Check if email is being updated and already exists
    if user_update.email and user_update.email != current_user.email:
        existing = await user_repo.get_by_email(user_update.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Check if username is being updated and already exists
    if user_update.username and user_update.username != current_user.username:
        existing = await user_repo.get_by_username(user_update.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    updated_user = await user_repo.update(current_user.id, user_update)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )

    logger.info("User profile updated", user_id=str(current_user.id))

    return UserResponse.model_validate(updated_user)


@router.put("/me/password", response_model=SuccessResponse)
async def update_my_password(
    password_update: UserUpdatePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """
    Update current user password.

    Args:
        password_update: Password update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        SuccessResponse: Update confirmation

    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not security_manager.verify_password(
        password_update.current_password, current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user_repo = UserRepository(db)
    success = await user_repo.update_password(current_user.id, password_update.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    logger.info("User password updated", user_id=str(current_user.id))

    return SuccessResponse(
        message="Password successfully updated",
    )


@router.delete("/me", response_model=SuccessResponse)
async def delete_my_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """
    Delete current user account.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        SuccessResponse: Deletion confirmation
    """
    user_repo = UserRepository(db)
    success = await user_repo.delete(current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        )

    logger.info("User account deleted", user_id=str(current_user.id))

    return SuccessResponse(
        message="Account successfully deleted",
    )


# Admin routes
@router.put("/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: UUID,
    user_update: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> UserResponse:
    """
    Update user as admin.

    Args:
        user_id: User ID to update
        user_update: Update data
        db: Database session
        current_user: Current admin user

    Returns:
        UserResponse: Updated user

    Raises:
        HTTPException: If user not found or insufficient permissions
    """
    user_repo = UserRepository(db)

    # Get target user
    target_user = await user_repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check permissions for role changes
    if user_update.role and user_update.role != target_user.role:
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can change user roles",
            )

    # Prevent demoting super admin
    if target_user.is_super_admin and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify super admin account",
        )

    updated_user = await user_repo.update(user_id, user_update, is_admin=True)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    logger.info("User updated by admin", user_id=str(user_id), admin_id=str(current_user.id))

    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", response_model=SuccessResponse)
async def admin_delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_super_admin_user),
) -> SuccessResponse:
    """
    Delete user as super admin.

    Args:
        user_id: User ID to delete
        db: Database session
        current_user: Current super admin user

    Returns:
        SuccessResponse: Deletion confirmation

    Raises:
        HTTPException: If user not found
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user_repo = UserRepository(db)
    success = await user_repo.delete(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info("User deleted by admin", user_id=str(user_id), admin_id=str(current_user.id))

    return SuccessResponse(
        message="User successfully deleted",
    )


@router.get("/{user_id}/posts", response_model=PostList)
async def get_user_posts(
    user_id: UUID,
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
) -> PostList:
    """
    Get posts by a specific user.

    Args:
        user_id: User ID
        pagination: Pagination parameters
        db: Database session

    Returns:
        PostList: User's posts
    """
    post_repo = PostRepository(db)

    offset = calculate_offset(pagination.page, pagination.page_size)

    posts, total = await post_repo.get_user_posts(
        user_id=user_id,
        skip=offset,
        limit=pagination.page_size,
        is_published=True,  # Only show published posts publicly
    )

    from src.schemas.post import PostResponse

    return PostList(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=calculate_pages(total, pagination.page_size),
    )
