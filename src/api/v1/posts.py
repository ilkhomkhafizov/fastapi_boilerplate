"""
Posts API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.post import PostRepository
from src.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostList,
    PostStats,
)
from src.schemas.common import SuccessResponse, PaginationParams
from src.models.user import User
from src.api.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    get_current_verified_user,
)
from src.api.dependencies.pagination import get_pagination_params, calculate_offset, calculate_pages
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
) -> PostResponse:
    """
    Create a new post.
    
    Args:
        post_data: Post creation data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        PostResponse: Created post
    """
    post_repo = PostRepository(db)
    post = await post_repo.create(post_data, current_user.id)
    
    logger.info("Post created", post_id=str(post.id), user_id=str(current_user.id))
    
    return PostResponse.model_validate(post)


@router.get("", response_model=PostList)
async def list_posts(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PostList:
    """
    List all published posts.
    
    Args:
        pagination: Pagination parameters
        is_featured: Filter by featured status
        search: Search query
        tag: Tag filter
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        PostList: Paginated list of posts
    """
    post_repo = PostRepository(db)
    
    offset = calculate_offset(pagination.page, pagination.page_size)
    
    # Only show published posts to non-authenticated users
    # Show all posts to authenticated users for their own posts
    posts, total = await post_repo.list_posts(
        skip=offset,
        limit=pagination.page_size,
        is_published=True,  # Always show only published posts in public list
        is_featured=is_featured,
        search=search,
        tag=tag,
        order_by=pagination.order_by or "published_at",
        order_desc=pagination.order_direction.value == "desc",
    )
    
    return PostList(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=calculate_pages(total, pagination.page_size),
    )


@router.get("/my", response_model=PostList)
async def get_my_posts(
    pagination: PaginationParams = Depends(get_pagination_params),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostList:
    """
    Get current user's posts.
    
    Args:
        pagination: Pagination parameters
        is_published: Filter by published status
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        PostList: User's posts
    """
    post_repo = PostRepository(db)
    
    offset = calculate_offset(pagination.page, pagination.page_size)
    
    posts, total = await post_repo.get_user_posts(
        user_id=current_user.id,
        skip=offset,
        limit=pagination.page_size,
        is_published=is_published,
    )
    
    return PostList(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=calculate_pages(total, pagination.page_size),
    )


@router.get("/featured", response_model=list[PostResponse])
async def get_featured_posts(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of posts"),
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """
    Get featured posts.
    
    Args:
        limit: Maximum number of posts
        db: Database session
    
    Returns:
        list[PostResponse]: Featured posts
    """
    post_repo = PostRepository(db)
    posts = await post_repo.get_featured_posts(limit)
    
    return [PostResponse.model_validate(post) for post in posts]


@router.get("/popular", response_model=list[PostResponse])
async def get_popular_posts(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of posts"),
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """
    Get popular posts by view count.
    
    Args:
        limit: Maximum number of posts
        db: Database session
    
    Returns:
        list[PostResponse]: Popular posts
    """
    post_repo = PostRepository(db)
    posts = await post_repo.get_popular_posts(limit)
    
    return [PostResponse.model_validate(post) for post in posts]


@router.get("/stats", response_model=PostStats)
async def get_post_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PostStats:
    """
    Get post statistics.
    
    Args:
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        PostStats: Post statistics
    """
    post_repo = PostRepository(db)
    
    # Get stats for current user if authenticated, otherwise global stats
    stats = await post_repo.get_post_stats(
        user_id=current_user.id if current_user else None
    )
    
    return PostStats(**stats)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PostResponse:
    """
    Get post by ID.
    
    Args:
        post_id: Post ID
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        PostResponse: Post details
    
    Raises:
        HTTPException: If post not found or not accessible
    """
    post_repo = PostRepository(db)
    post = await post_repo.get_by_id(post_id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    # Check if post is accessible
    if not post.is_published:
        # Only author and admins can view unpublished posts
        if not current_user or (
            post.author_id != current_user.id and not current_user.is_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
    
    # Increment view count for published posts
    if post.is_published:
        await post_repo.increment_view_count(post_id)
    
    return PostResponse.model_validate(post)


@router.get("/slug/{slug}", response_model=PostResponse)
async def get_post_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PostResponse:
    """
    Get post by slug.
    
    Args:
        slug: Post slug
        db: Database session
        current_user: Current user (optional)
    
    Returns:
        PostResponse: Post details
    
    Raises:
        HTTPException: If post not found or not accessible
    """
    post_repo = PostRepository(db)
    post = await post_repo.get_by_slug(slug)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    # Check if post is accessible
    if not post.is_published:
        # Only author and admins can view unpublished posts
        if not current_user or (
            post.author_id != current_user.id and not current_user.is_admin
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
    
    # Increment view count for published posts
    if post.is_published:
        await post_repo.increment_view_count(post.id)
    
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    """
    Update post.
    
    Args:
        post_id: Post ID
        post_update: Update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        PostResponse: Updated post
    
    Raises:
        HTTPException: If post not found or user lacks permission
    """
    post_repo = PostRepository(db)
    post = await post_repo.get_by_id(post_id, with_author=False)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    # Check permissions
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this post",
        )
    
    updated_post = await post_repo.update(post_id, post_update)
    
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update post",
        )
    
    logger.info("Post updated", post_id=str(post_id), user_id=str(current_user.id))
    
    return PostResponse.model_validate(updated_post)


@router.delete("/{post_id}", response_model=SuccessResponse)
async def delete_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """
    Delete post.
    
    Args:
        post_id: Post ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        SuccessResponse: Deletion confirmation
    
    Raises:
        HTTPException: If post not found or user lacks permission
    """
    post_repo = PostRepository(db)
    post = await post_repo.get_by_id(post_id, with_author=False)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    # Check permissions
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this post",
        )
    
    success = await post_repo.delete(post_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete post",
        )
    
    logger.info("Post deleted", post_id=str(post_id), user_id=str(current_user.id))
    
    return SuccessResponse(
        message="Post successfully deleted",
    )
