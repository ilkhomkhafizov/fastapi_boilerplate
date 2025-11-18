"""
API v1 router aggregator.
"""

from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router
from src.api.v1.posts import router as posts_router
from src.api.v1.health import router as health_router

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(posts_router)
