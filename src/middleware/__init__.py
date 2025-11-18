"""
Middleware for request processing, logging, and error handling.
"""

import time
import uuid
from typing import Callable
from contextvars import ContextVar

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to context and headers."""
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
                process_time=round(process_time, 3),
            )
            raise
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time=round(process_time, 3),
        )
        
        # Add process time to headers
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions and return appropriate error responses."""
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            logger.error("Validation error", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "success": False,
                    "message": "Validation error",
                    "detail": str(e),
                },
            )
        except Exception as e:
            logger.error("Unhandled exception", error=str(e), exc_info=True)
            
            # Don't expose internal errors in production
            if settings.is_production:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "message": "Internal server error",
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "message": "Internal server error",
                        "detail": str(e),
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    },
                )


def get_cors_middleware() -> CORSMiddleware:
    """
    Get CORS middleware with configuration from settings.
    
    Returns:
        CORSMiddleware: Configured CORS middleware
    """
    return CORSMiddleware(
        app=None,  # Will be set when added to app
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
