"""
Logging configuration module.
Sets up structured logging with JSON format for production.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory
from pythonjsonlogger import jsonlogger

from src.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    """
    # Set log level based on configuration
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Create custom JSON formatter for production
    if settings.is_production:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # Apply JSON formatter to all handlers
        for handler in logging.root.handlers:
            handler.setFormatter(formatter)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ) if settings.debug else structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() if settings.is_production
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


# Correlation ID context manager
class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to the log record."""
        from contextvars import ContextVar
        correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
        record.correlation_id = correlation_id.get()
        return True


# Add correlation ID filter to all handlers
def add_correlation_id_filter() -> None:
    """Add correlation ID filter to all log handlers."""
    correlation_filter = CorrelationIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(correlation_filter)


# Initialize logging on module import
setup_logging()
add_correlation_id_filter()

# Export commonly used logger
logger = get_logger(__name__)
