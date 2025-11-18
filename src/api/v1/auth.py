"""
Authentication API routes.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user
from src.core.database import get_db
from src.core.logging import get_logger
from src.core.redis import redis_manager
from src.core.security import security_manager
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.auth import (
    EmailVerificationRequest,
    LoginRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
)
from src.schemas.common import SuccessResponse
from src.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user

    Raises:
        HTTPException: If email or username already exists
    """
    user_repo = UserRepository(db)

    # Check if email exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username exists
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = await user_repo.create(user_data)

    logger.info("User registered", user_id=str(user.id), email=user.email)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login user and get access token.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Token: Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)

    # Get user by email
    user = await user_repo.get_by_email(login_data.email)

    if not user or not security_manager.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = security_manager.create_access_token(
        data={"sub": str(user.id), "email": user.email},
    )
    refresh_token = security_manager.create_refresh_token(data={"sub": str(user.id)})

    # Update last login
    await user_repo.update_last_login(user.id)

    # Store refresh token in Redis (optional)
    await redis_manager.set(
        f"refresh_token:{user.id}", refresh_token, expire=7 * 24 * 3600,  # 7 days
    )

    logger.info("User logged in", user_id=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token
        db: Database session

    Returns:
        Token: New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = security_manager.verify_token(refresh_data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify refresh token in Redis
    stored_token = await redis_manager.get(f"refresh_token:{user_id}")
    if stored_token != refresh_data.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = security_manager.create_access_token(
        data={"sub": str(user.id), "email": user.email},
    )
    new_refresh_token = security_manager.create_refresh_token(data={"sub": str(user.id)})

    # Update refresh token in Redis
    await redis_manager.set(f"refresh_token:{user.id}", new_refresh_token, expire=7 * 24 * 3600)

    logger.info("Token refreshed", user_id=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """
    Logout current user.

    Args:
        current_user: Current authenticated user

    Returns:
        SuccessResponse: Logout confirmation
    """
    # Remove refresh token from Redis
    await redis_manager.delete(f"refresh_token:{current_user.id}")

    logger.info("User logged out", user_id=str(current_user.id))

    return SuccessResponse(
        message="Successfully logged out",
    )


@router.post("/password-reset", response_model=SuccessResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Request password reset.

    Args:
        reset_data: Password reset request data
        db: Database session

    Returns:
        SuccessResponse: Confirmation message
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(reset_data.email)

    if user:
        # Create reset token
        reset_token = security_manager.create_access_token(
            data={"sub": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1),
        )

        # Store in Redis
        await redis_manager.set(f"password_reset:{user.id}", reset_token, expire=3600)  # 1 hour

        # TODO: Send email with reset token
        logger.info("Password reset requested", user_id=str(user.id))

    # Always return success to prevent email enumeration
    return SuccessResponse(
        message="If the email exists, a password reset link has been sent",
    )


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Verify user email.

    Args:
        verification_data: Email verification token
        db: Database session

    Returns:
        SuccessResponse: Verification confirmation

    Raises:
        HTTPException: If token is invalid
    """
    payload = security_manager.decode_token(verification_data.token)

    if not payload or payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload",
        )

    user_repo = UserRepository(db)
    success = await user_repo.verify_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info("Email verified", user_id=str(user_id))

    return SuccessResponse(
        message="Email successfully verified",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: User information
    """
    return UserResponse.model_validate(current_user)
