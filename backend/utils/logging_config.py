
import logging
import sys
import os
import structlog
from typing import Any, Dict

def configure_structlog():
    """
    Configure structured logging for the application.
    Uses structlog to output JSON logs in production and colored logs in development.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if environment == "production":
        # JSON logs for production (better for aggregation tools like ELK, Datadog)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty colored logs for local development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
        cache_logger_on_first_use=True,
    )
    
    # Intercept standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )
    
    # Redirect standard logging to structlog
    # This ensures third-party libraries also get formatted (mostly)
    
    return structlog.get_logger()

# Global logger instance
logger = configure_structlog()
