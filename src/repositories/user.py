"""
User repository for database operations.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.security import security_manager
from src.models.user import User, UserRole
from src.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.

        Args:
            db: Database session
        """
        self.db = db

    async def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            User: Created user
        """
        # Hash password
        hashed_password = security_manager.hash_password(user_data.password)

        # Create user instance
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            bio=user_data.bio,
            hashed_password=hashed_password,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User created", user_id=str(user.id), email=user.email)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: User if found
        """
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            Optional[User]: User if found
        """
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            Optional[User]: User if found
        """
        query = select(User).where(User.username == username.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(self, identifier: str) -> User | None:
        """
        Get user by email or username.

        Args:
            identifier: Email or username

        Returns:
            Optional[User]: User if found
        """
        identifier_lower = identifier.lower()
        query = select(User).where(
            or_(User.email == identifier_lower, User.username == identifier_lower),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, user_id: UUID, user_data: UserUpdate, is_admin: bool = False,
    ) -> User | None:
        """
        Update user.

        Args:
            user_id: User ID
            user_data: Update data
            is_admin: Whether update is by admin

        Returns:
            Optional[User]: Updated user if found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User updated", user_id=str(user_id))
        return user

    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """
        Update user password.

        Args:
            user_id: User ID
            new_password: New password (plain text)

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.hashed_password = security_manager.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info("User password updated", user_id=str(user_id))
        return True

    async def update_last_login(self, user_id: UUID) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def delete(self, user_id: UUID) -> bool:
        """
        Delete user.

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()

        logger.info("User deleted", user_id=str(user_id))
        return True

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """
        List users with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status
            role: Filter by role
            search: Search in email and username

        Returns:
            tuple: List of users and total count
        """
        # Base query
        query = select(User)
        count_query = select(func.count()).select_from(User)

        # Apply filters
        filters = []

        if is_active is not None:
            filters.append(User.is_active == is_active)

        if role is not None:
            filters.append(User.role == role)

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    User.email.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                ),
            )

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(User.created_at.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        return users, total

    async def verify_user(self, user_id: UUID) -> bool:
        """
        Verify user email.

        Args:
            user_id: User ID

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_verified = True
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info("User verified", user_id=str(user_id))
        return True

    async def activate_user(self, user_id: UUID, activate: bool = True) -> bool:
        """
        Activate or deactivate user.

        Args:
            user_id: User ID
            activate: Whether to activate or deactivate

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = activate
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        action = "activated" if activate else "deactivated"
        logger.info("User %s", action, user_id=str(user_id))
        return True

    async def change_role(self, user_id: UUID, new_role: UserRole) -> bool:
        """
        Change user role.

        Args:
            user_id: User ID
            new_role: New role

        Returns:
            bool: Success status
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info("User role changed", user_id=str(user_id), old_role=old_role, new_role=new_role)
        return True

    async def count_by_role(self) -> dict[UserRole, int]:
        """
        Count users by role.

        Returns:
            dict: User count by role
        """
        query = select(User.role, func.count(User.id)).group_by(User.role)

        result = await self.db.execute(query)
        counts = {role: count for role, count in result}

        return counts
