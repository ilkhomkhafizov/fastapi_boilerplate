"""
Redis configuration and client management.
Provides async Redis client with connection pooling.
"""

from typing import Optional, Any
import json
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisManager:
    """Manages Redis connections and operations."""
    
    def __init__(self) -> None:
        """Initialize Redis manager."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def create_pool(self) -> ConnectionPool:
        """
        Create Redis connection pool.
        
        Returns:
            ConnectionPool: Redis connection pool
        """
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=50,
                decode_responses=True,  # Decode bytes to strings
                health_check_interval=30,
            )
            logger.info("Redis connection pool created")
        
        return self._pool
    
    async def get_client(self) -> redis.Redis:
        """
        Get Redis client.
        
        Returns:
            redis.Redis: Async Redis client
        """
        if self._client is None:
            pool = await self.create_pool()
            self._client = redis.Redis(connection_pool=pool)
            
            # Test connection
            try:
                await self._client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                raise
        
        return self._client
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
            logger.info("Redis client closed")
        
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis connection pool disconnected")
    
    # Cache operations
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Optional[Any]: Cached value or None
        """
        client = await self.get_client()
        value = await client.get(key)
        
        if value:
            try:
                # Try to deserialize JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        
        Returns:
            bool: Success status
        """
        client = await self.get_client()
        
        # Serialize value to JSON if not string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        return await client.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if key was deleted
        """
        client = await self.get_client()
        result = await client.delete(key)
        return bool(result)
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if key exists
        """
        client = await self.get_client()
        return bool(await client.exists(key))
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
        
        Returns:
            bool: True if expiration was set
        """
        client = await self.get_client()
        return await client.expire(key, seconds)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment counter.
        
        Args:
            key: Counter key
            amount: Increment amount
        
        Returns:
            int: New counter value
        """
        client = await self.get_client()
        return await client.incrby(key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement counter.
        
        Args:
            key: Counter key
            amount: Decrement amount
        
        Returns:
            int: New counter value
        """
        client = await self.get_client()
        return await client.decrby(key, amount)
    
    @asynccontextmanager
    async def lock(
        self,
        key: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None
    ):
        """
        Distributed lock using Redis.
        
        Args:
            key: Lock key
            timeout: Lock timeout in seconds
            blocking: Whether to block waiting for lock
            blocking_timeout: Maximum time to wait for lock
        
        Yields:
            Lock instance
        """
        client = await self.get_client()
        lock = client.lock(
            f"lock:{key}",
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout
        )
        
        try:
            await lock.acquire()
            yield lock
        finally:
            try:
                await lock.release()
            except Exception:
                pass  # Lock might have expired


# Create global Redis manager instance
redis_manager = RedisManager()


# Dependency for FastAPI
async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client.
    
    Returns:
        redis.Redis: Redis client
    """
    return await redis_manager.get_client()
