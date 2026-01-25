"""
MatruRaksha - Health Check Routes
Endpoints for monitoring system health and readiness
"""

import os
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

# Will be injected from main.py
supabase_client = None
gemini_client = None
bot_running_flag = False
cache_instance = None

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check - returns 200 if server is running
    Used by load balancers for liveness probes
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MatruRaksha API",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }


@router.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """
    Readiness check - returns 200 only if all dependencies are healthy
    Used by load balancers to determine if instance can receive traffic
    """
    from utils.health_checks import check_all_dependencies, is_system_healthy
    
    # Check all dependencies
    checks = await check_all_dependencies(
        supabase_client=supabase_client,
        gemini_client=gemini_client,
        bot_running=bot_running_flag,
        cache=cache_instance
    )
    
    # Determine overall health
    healthy = is_system_healthy(checks)
    
    response_data = {
        "status": "ready" if healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    # Return 200 if healthy, 503 if not ready
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def set_health_check_dependencies(supabase, gemini, bot_running, cache):
    """
    Inject dependencies for health checks
    Called from main.py during startup
    """
    global supabase_client, gemini_client, bot_running_flag, cache_instance
    
    supabase_client = supabase
    gemini_client = gemini
    bot_running_flag = bot_running
    cache_instance = cache
