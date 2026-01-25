"""
MatruRaksha - Custom Exceptions
Structured exception hierarchy for better error handling and client responses
"""

from typing import Optional, Dict, Any


class MatruRakshaException(Exception):
    """Base exception for all MatruRaksha errors"""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MatruRakshaException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, **(details or {})}
        )


class AuthenticationError(MatruRakshaException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(MatruRakshaException):
    """Raised when user lacks permission"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403
        )


class NotFoundError(MatruRakshaException):
    """Raised when resource not found"""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class ConflictError(MatruRakshaException):
    """Raised on data conflicts (e.g., duplicate entries, version conflicts)"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class ExternalServiceError(MatruRakshaException):
    """Raised when external service (Gemini, Supabase, etc.) fails"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=503,
            details={"service": service, **(details or {})}
        )


class DatabaseError(MatruRakshaException):
    """Raised on database operation failures"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation}
        )


class RateLimitExceededError(MatruRakshaException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )


class FileValidationError(MatruRakshaException):
    """Raised when file upload validation fails"""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            code="FILE_VALIDATION_ERROR",
            status_code=400,
            details={"filename": filename}
        )
