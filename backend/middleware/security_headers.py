
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Implements: HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, CSP
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict-Transport-Security (HSTS) - Enforce HTTPS
        # Max-age: 1 year (31536000 seconds)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Frame-Options - Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - Prevent MIME Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection - Enable XSS filtering (legacy but good defense in depth)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy (CSP) - Reduce XSS risks
        # Note: This is a strict policy, might need adjustment for specialized integrations
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline/eval for React/Swagger
            "style-src 'self' 'unsafe-inline'; "
            "frame-ancestors 'none'; "
            "object-src 'none';"
        )
        
        # Referrer-Policy - Privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy - Limit browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

def setup_security_headers(app: FastAPI):
    """Register security middleware"""
    app.add_middleware(SecurityHeadersMiddleware)
