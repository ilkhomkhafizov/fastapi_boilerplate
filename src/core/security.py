"""
Security utilities for authentication and authorization.
Provides password hashing and JWT token management.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Manages security operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.access_token_expire_minutes,
            )

        to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "access"})

        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: dict[str, Any], expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

        to_encode.update({"exp": expire, "iat": datetime.now(UTC), "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token

        Returns:
            Optional[Dict[str, Any]]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload
        except JWTError as e:
            logger.warning("JWT decode error", error=str(e))
            return None

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
        """
        Verify token and check type.

        Args:
            token: JWT token
            token_type: Expected token type

        Returns:
            Optional[Dict[str, Any]]: Token payload if valid
        """
        payload = SecurityManager.decode_token(token)

        if payload and payload.get("type") == token_type:
            return payload

        return None


# Create global security manager instance
security_manager = SecurityManager()
