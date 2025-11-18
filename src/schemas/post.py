"""
Post schemas for request/response validation.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.user import UserResponse


class PostBase(BaseModel):
    """Base post schema."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    summary: str | None = Field(None, max_length=500)
    tags: list[str] | None = Field(default_factory=list)
    is_published: bool = False
    is_featured: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Clean and validate title."""
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate and clean tags."""
        if v:
            # Remove duplicates and clean
            return list(set(tag.strip().lower() for tag in v if tag.strip()))
        return v


class PostCreate(PostBase):
    """Schema for creating a new post."""

    slug: str | None = Field(None, min_length=1, max_length=250)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None, values) -> str:
        """Generate or validate slug."""
        if v:
            # Validate provided slug
            if not re.match(r"^[a-z0-9-]+$", v):
                raise ValueError("Slug can only contain lowercase letters, numbers, and hyphens")
            return v
        # Generate slug from title if not provided
        title = values.data.get("title", "")
        if title:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
            slug = slug.strip("-")
            return slug[:250]
        return v


class PostUpdate(BaseModel):
    """Schema for updating a post."""

    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = Field(None, min_length=10)
    summary: str | None = Field(None, max_length=500)
    tags: list[str] | None = None
    is_published: bool | None = None
    is_featured: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Clean and validate title."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        """Validate and clean tags."""
        if v is not None:
            return list(set(tag.strip().lower() for tag in v if tag.strip()))
        return v


class PostInDB(PostBase):
    """Post schema with database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    author_id: UUID
    view_count: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None


class PostResponse(PostInDB):
    """Post response schema (public)."""

    author: UserResponse | None = None


class PostList(BaseModel):
    """List of posts response."""

    items: list[PostResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PostStats(BaseModel):
    """Post statistics."""

    total_posts: int
    published_posts: int
    featured_posts: int
    total_views: int
    avg_views_per_post: float
