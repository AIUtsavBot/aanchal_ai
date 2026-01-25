"""
MatruRaksha - Rate Limiting Configuration
Implements API rate limiting to prevent abuse and DDoS attacks
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"],  # Global default
    headers_enabled=True,
    storage_uri="memory://"  # Use in-memory storage (upgrade to Redis in production)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors
    Returns 429 with retry-after header
    """
    logger.warning(
        f"Rate limit exceeded",
        extra={
            "path": request.url.path,
            "client_ip": get_remote_address(request),
            "limit": str(exc.detail)
        }
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": 60  # seconds
                }
            }
        },
        headers={
            "Retry-After": "60"
        }
    )


def setup_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI app
    """
    # Add rate limiter state to app
    app.state.limiter = limiter
    
    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    # Add middleware
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("✅ Rate limiting configured")


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "auth_login": "5/minute",        # Login attempts
    "auth_signup": "3/minute",       # Signup attempts
    "agent_query": "10/minute",      # AI agent queries
    "risk_assessment": "20/minute",  # Risk assessments
    "file_upload": "10/minute",      # File uploads
    "general_read": "100/minute",    # General GET requests
    "general_write": "30/minute",    # General POST/PUT requests
}
