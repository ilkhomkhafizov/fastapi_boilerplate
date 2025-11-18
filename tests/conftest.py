"""
Test configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.core.database import Base, db_manager
from src.core.config import settings
from src.models.user import User, UserRole
from src.repositories.user import UserRepository
from src.core.security import security_manager


# Override settings for testing
settings.environment = "testing"
settings.debug = True


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    # Create test engine
    engine = create_async_engine(
        settings.async_database_url.replace("fastapi_db", "fastapi_test_db"),
        poolclass=NullPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client.
    
    Args:
        test_db: Test database session
    
    Yields:
        AsyncClient: Test client
    """
    # Override database dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[db_manager.get_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """
    Create test user.
    
    Args:
        test_db: Test database session
    
    Returns:
        User: Test user
    """
    user_repo = UserRepository(test_db)
    
    from src.schemas.user import UserCreate
    
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="TestPass123!",
        full_name="Test User",
    )
    
    user = await user_repo.create(user_data)
    user.is_verified = True
    await test_db.commit()
    
    return user


@pytest_asyncio.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """
    Create test admin user.
    
    Args:
        test_db: Test database session
    
    Returns:
        User: Test admin user
    """
    user_repo = UserRepository(test_db)
    
    from src.schemas.user import UserCreate
    
    user_data = UserCreate(
        email="admin@example.com",
        username="adminuser",
        password="AdminPass123!",
        full_name="Admin User",
    )
    
    user = await user_repo.create(user_data)
    user.is_verified = True
    user.role = UserRole.ADMIN
    await test_db.commit()
    
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """
    Create authentication headers for test user.
    
    Args:
        test_user: Test user
    
    Returns:
        dict: Authentication headers
    """
    token = security_manager.create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin: User) -> dict:
    """
    Create authentication headers for admin user.
    
    Args:
        test_admin: Test admin user
    
    Returns:
        dict: Authentication headers
    """
    token = security_manager.create_access_token(
        data={"sub": str(test_admin.id), "email": test_admin.email}
    )
    return {"Authorization": f"Bearer {token}"}
