"""
MatruRaksha - Error Handlers
FastAPI exception handlers for consistent error responses
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from core.exceptions import MatruRakshaException

logger = logging.getLogger(__name__)


async def matruraksha_exception_handler(request: Request, exc: MatruRakshaException) -> JSONResponse:
    """Handle custom MatruRaksha exceptions"""
    
    # Log the error
    logger.error(
        f"MatruRaksha error: {exc.code}",
        extra={
            "code": exc.code,
            "message": exc.message,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )
    
    # Return structured error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error: {errors}",
        extra={
            "path": request.url.path,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {
                    "errors": errors
                }
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    
    # Log the full exception
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return generic error (don't leak stack traces)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred. Please try again later."
            }
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    
    app.add_exception_handler(MatruRakshaException, matruraksha_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("✅ Exception handlers registered")
