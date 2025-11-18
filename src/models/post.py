"""
Post model definition.
Example model to demonstrate relationships and features.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Post(Base):
    """Post model."""
    
    __tablename__ = "posts"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    # Post content
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    slug: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Metadata
    tags: Mapped[Optional[str]] = mapped_column(
        Text,  # Store as JSON string
        nullable=True
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Status
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Foreign keys
    author_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_posts_author_published", "author_id", "is_published"),
        Index("ix_posts_created_at_published", "created_at", "is_published"),
        Index("ix_posts_slug_published", "slug", "is_published"),
    )
    
    def __repr__(self) -> str:
        """String representation of Post."""
        return f"<Post(id={self.id}, title={self.title}, author_id={self.author_id})>"
    
    @property
    def is_editable_by(self, user: "User") -> bool:
        """Check if post can be edited by user."""
        return user.id == self.author_id or user.is_admin
