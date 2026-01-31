"""
MatruRaksha - Health Check Utilities
Helper functions to check system dependencies
"""

import asyncio
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_database(supabase_client) -> Dict[str, any]:
    """Check Supabase database connectivity"""
    try:
        # Try to query a simple table
        result = supabase_client.table("mothers").select("id").limit(1).execute()
        
        return {
            "status": "healthy",
            "latency_ms": 0,  # Could add timing here
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }


async def check_gemini_api(gemini_client) -> Dict[str, any]:
    """Check Gemini API availability"""
    try:
        if not gemini_client:
            return {
                "status": "unavailable",
                "message": "Gemini client not initialized"
            }
        
        # Simple ping - try to generate minimal content
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents="test"
        )
        
        return {
            "status": "healthy",
            "message": "Gemini API responding"
        }
    except Exception as e:
        logger.warning(f"Gemini API health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Gemini API unavailable"
        }


async def check_telegram_bot(bot_running: bool) -> Dict[str, any]:
    """Check Telegram bot status"""
    if bot_running:
        return {
            "status": "healthy",
            "message": "Telegram bot is running"
        }
    else:
        return {
            "status": "stopped",
            "message": "Telegram bot is not running"
        }


async def check_cache_service(cache) -> Dict[str, any]:
    """Check cache service"""
    try:
        if not cache:
            return {
                "status": "unavailable",
                "message": "Cache service not initialized"
            }
        
        # Get cache stats
        stats = cache.stats()
        
        return {
            "status": "healthy",
            "message": f"Cache active with {stats['active_entries']} entries",
            "details": stats
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_all_dependencies(
    supabase_client,
    gemini_client,
    bot_running: bool,
    cache
) -> Dict[str, Dict]:
    """Check all system dependencies"""
    
    # Run all checks in parallel
    database_check, gemini_check, telegram_check, cache_check = await asyncio.gather(
        check_database(supabase_client),
        check_gemini_api(gemini_client),
        check_telegram_bot(bot_running),
        check_cache_service(cache),
        return_exceptions=True
    )
    
    return {
        "database": database_check if not isinstance(database_check, Exception) else {"status": "error", "error": str(database_check)},
        "gemini_api": gemini_check if not isinstance(gemini_check, Exception) else {"status": "error", "error": str(gemini_check)},
        "telegram_bot": telegram_check if not isinstance(telegram_check, Exception) else {"status": "error", "error": str(telegram_check)},
        "cache": cache_check if not isinstance(cache_check, Exception) else {"status": "error", "error": str(cache_check)}
    }


def is_system_healthy(checks: Dict[str, Dict]) -> bool:
    """Determine if system is healthy based on dependency checks"""
    
    # Critical dependencies
    critical = ["database"]
    
    for service in critical:
        if service in checks and checks[service].get("status") != "healthy":
            return False
    
    return True
