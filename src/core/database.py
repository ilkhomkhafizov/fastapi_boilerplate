"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with async support.
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import MetaData

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Naming convention for database constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Create declarative base
Base = declarative_base(metadata=metadata)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self) -> None:
        """Initialize database manager."""
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
    
    async def create_engine(self) -> AsyncEngine:
        """
        Create and configure async database engine.
        
        Returns:
            AsyncEngine: Configured database engine
        """
        if self._engine is None:
            # Engine configuration
            engine_config = {
                "echo": settings.debug,
                "echo_pool": settings.debug,
                "pool_pre_ping": True,  # Verify connections before using
                "pool_size": 10,  # Number of connections to maintain
                "max_overflow": 20,  # Maximum overflow connections
                "pool_recycle": 3600,  # Recycle connections after 1 hour
            }
            
            # Use NullPool for testing
            if settings.is_testing:
                engine_config["poolclass"] = NullPool
            
            self._engine = create_async_engine(
                settings.async_database_url,
                **engine_config
            )
            
            logger.info("Database engine created", url=settings.async_database_url.split("@")[1])
        
        return self._engine
    
    async def create_sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        """
        Create async session maker.
        
        Returns:
            async_sessionmaker: Session maker for creating database sessions
        """
        if self._sessionmaker is None:
            engine = await self.create_engine()
            self._sessionmaker = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autocommit=False,
                autoflush=False,
            )
            logger.info("Session maker created")
        
        return self._sessionmaker
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session.
        
        Yields:
            AsyncSession: Database session
        """
        sessionmaker = await self.create_sessionmaker()
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions.
        
        Yields:
            AsyncSession: Database session
        """
        sessionmaker = await self.create_sessionmaker()
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def init_db(self) -> None:
        """Initialize database (create tables)."""
        engine = await self.create_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
    
    async def drop_db(self) -> None:
        """Drop all database tables."""
        engine = await self.create_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("Database tables dropped")
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")


# Create global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in db_manager.get_session():
        yield session
