"""
Post repository for database operations.
"""

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.logging import get_logger
from src.models.post import Post
from src.schemas.post import PostCreate, PostUpdate

logger = get_logger(__name__)


class PostRepository:
    """Repository for post database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize post repository.

        Args:
            db: Database session
        """
        self.db = db

    async def create(self, post_data: PostCreate, author_id: UUID) -> Post:
        """
        Create a new post.

        Args:
            post_data: Post creation data
            author_id: Author's user ID

        Returns:
            Post: Created post
        """
        # Prepare post data
        post_dict = post_data.model_dump()

        # Convert tags list to JSON string
        if post_dict.get("tags"):
            post_dict["tags"] = json.dumps(post_dict["tags"])

        # Generate slug if not provided
        if not post_dict.get("slug"):
            import re

            base_slug = re.sub(r"[^a-z0-9]+", "-", post_data.title.lower()).strip("-")

            # Check for duplicate slugs
            count = 0
            slug = base_slug
            while await self.get_by_slug(slug):
                count += 1
                slug = f"{base_slug}-{count}"
            post_dict["slug"] = slug

        # Create post instance
        post = Post(
            **post_dict,
            author_id=author_id,
            published_at=datetime.utcnow() if post_data.is_published else None,
        )

        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)

        # Load relationships
        await self.db.refresh(post, ["author"])

        logger.info("Post created", post_id=str(post.id), slug=post.slug)
        return post

    async def get_by_id(self, post_id: UUID, with_author: bool = True) -> Post | None:
        """
        Get post by ID.

        Args:
            post_id: Post ID
            with_author: Whether to load author relationship

        Returns:
            Optional[Post]: Post if found
        """
        query = select(Post).where(Post.id == post_id)

        if with_author:
            query = query.options(selectinload(Post.author))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, with_author: bool = True) -> Post | None:
        """
        Get post by slug.

        Args:
            slug: Post slug
            with_author: Whether to load author relationship

        Returns:
            Optional[Post]: Post if found
        """
        query = select(Post).where(Post.slug == slug)

        if with_author:
            query = query.options(selectinload(Post.author))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, post_id: UUID, post_data: PostUpdate) -> Post | None:
        """
        Update post.

        Args:
            post_id: Post ID
            post_data: Update data

        Returns:
            Optional[Post]: Updated post if found
        """
        post = await self.get_by_id(post_id)
        if not post:
            return None

        # Update fields
        update_data = post_data.model_dump(exclude_unset=True)

        # Convert tags list to JSON string
        if "tags" in update_data:
            update_data["tags"] = json.dumps(update_data["tags"])

        # Update published_at if publishing status changes
        if "is_published" in update_data:
            if update_data["is_published"] and not post.is_published:
                update_data["published_at"] = datetime.utcnow()
            elif not update_data["is_published"]:
                update_data["published_at"] = None

        for field, value in update_data.items():
            setattr(post, field, value)

        post.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(post)

        # Reload with author
        await self.db.refresh(post, ["author"])

        logger.info("Post updated", post_id=str(post_id))
        return post

    async def delete(self, post_id: UUID) -> bool:
        """
        Delete post.

        Args:
            post_id: Post ID

        Returns:
            bool: Success status
        """
        post = await self.get_by_id(post_id, with_author=False)
        if not post:
            return False

        await self.db.delete(post)
        await self.db.commit()

        logger.info("Post deleted", post_id=str(post_id))
        return True

    async def increment_view_count(self, post_id: UUID) -> bool:
        """
        Increment post view count.

        Args:
            post_id: Post ID

        Returns:
            bool: Success status
        """
        stmt = update(Post).where(Post.id == post_id).values(view_count=Post.view_count + 1)

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount > 0

    async def list_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        is_published: bool | None = None,
        is_featured: bool | None = None,
        author_id: UUID | None = None,
        search: str | None = None,
        tag: str | None = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> tuple[list[Post], int]:
        """
        List posts with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            is_published: Filter by published status
            is_featured: Filter by featured status
            author_id: Filter by author
            search: Search in title and content
            tag: Filter by tag
            order_by: Field to order by
            order_desc: Whether to order descending

        Returns:
            tuple: List of posts and total count
        """
        # Base query with author relationship
        query = select(Post).options(selectinload(Post.author))
        count_query = select(func.count()).select_from(Post)

        # Apply filters
        filters = []

        if is_published is not None:
            filters.append(Post.is_published == is_published)

        if is_featured is not None:
            filters.append(Post.is_featured == is_featured)

        if author_id is not None:
            filters.append(Post.author_id == author_id)

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Post.title.ilike(search_pattern),
                    Post.content.ilike(search_pattern),
                    Post.summary.ilike(search_pattern),
                ),
            )

        if tag:
            # Search in JSON tags field
            filters.append(Post.tags.contains(f'"{tag.lower()}"'))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply ordering
        order_field = getattr(Post, order_by, Post.created_at)
        if order_desc:
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        posts = result.scalars().all()

        return posts, total

    async def get_user_posts(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        is_published: bool | None = None,
    ) -> tuple[list[Post], int]:
        """
        Get posts by a specific user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            is_published: Filter by published status

        Returns:
            tuple: List of posts and total count
        """
        return await self.list_posts(
            skip=skip,
            limit=limit,
            author_id=user_id,
            is_published=is_published,
        )

    async def get_featured_posts(self, limit: int = 10) -> list[Post]:
        """
        Get featured posts.

        Args:
            limit: Maximum number of posts

        Returns:
            List[Post]: Featured posts
        """
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .where(and_(Post.is_published == True, Post.is_featured == True))
            .order_by(Post.published_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_popular_posts(self, limit: int = 10) -> list[Post]:
        """
        Get popular posts by view count.

        Args:
            limit: Maximum number of posts

        Returns:
            List[Post]: Popular posts
        """
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .where(Post.is_published == True)
            .order_by(Post.view_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_post_stats(self, user_id: UUID | None = None) -> dict:
        """
        Get post statistics.

        Args:
            user_id: Optional user ID to filter stats

        Returns:
            dict: Post statistics
        """
        base_filter = []
        if user_id:
            base_filter.append(Post.author_id == user_id)

        # Total posts
        total_query = select(func.count(Post.id))
        if base_filter:
            total_query = total_query.where(and_(*base_filter))
        total_result = await self.db.execute(total_query)
        total_posts = total_result.scalar() or 0

        # Published posts
        published_query = select(func.count(Post.id)).where(
            and_(Post.is_published == True, *base_filter),
        )
        published_result = await self.db.execute(published_query)
        published_posts = published_result.scalar() or 0

        # Featured posts
        featured_query = select(func.count(Post.id)).where(
            and_(Post.is_featured == True, *base_filter),
        )
        featured_result = await self.db.execute(featured_query)
        featured_posts = featured_result.scalar() or 0

        # Total views
        views_query = select(func.sum(Post.view_count))
        if base_filter:
            views_query = views_query.where(and_(*base_filter))
        views_result = await self.db.execute(views_query)
        total_views = views_result.scalar() or 0

        # Average views
        avg_views = total_views / total_posts if total_posts > 0 else 0

        return {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "featured_posts": featured_posts,
            "total_views": total_views,
            "avg_views_per_post": round(avg_views, 2),
        }
