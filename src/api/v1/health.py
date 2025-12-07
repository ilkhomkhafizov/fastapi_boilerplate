"""
Health check API routes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.logging import get_logger
from src.core.redis import redis_manager
from src.schemas.common import HealthCheckResponse, AllHealthCheckResponse

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthCheckResponse:
    """
    Basic health check endpoint.

    Returns:
        HealthCheckResponse: Application health status
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/live", response_model=HealthCheckResponse)
async def liveness_probe() -> HealthCheckResponse:
    """
    Kubernetes liveness probe endpoint.

    Returns:
        HealthCheckResponse: Liveness status
    """
    return HealthCheckResponse(
        status="alive",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/ready", response_model=AllHealthCheckResponse)
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
) -> AllHealthCheckResponse:
    """
    Kubernetes readiness probe endpoint.
    Checks database and Redis connectivity.

    Args:
        db: Database session

    Returns:
        AllHealthCheckResponse: Readiness status with service checks
    """
    database_healthy = False
    redis_healthy = False

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        database_healthy = result.scalar() == 1
    except Exception as e:
        logger.error("Database health check failed", error=str(e))

    # Check Redis
    try:
        redis_client = await redis_manager.get_client()
        redis_healthy = await redis_client.ping()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))

    # Determine overall status
    overall_status = "healthy" if (database_healthy and redis_healthy) else "degraded"

    return AllHealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        database=database_healthy,
        redis=redis_healthy,
        timestamp=datetime.utcnow().isoformat(),
    )
