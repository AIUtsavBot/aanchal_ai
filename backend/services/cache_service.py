"""
MatruRaksha AI - In-Memory Cache Service
Simple TTL-based caching for dashboard performance (Free - No Redis needed)
"""

import time
import threading
from typing import Any, Optional, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("✅ In-memory cache initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry["expires_at"]:
                    logger.debug(f"Cache HIT: {key}")
                    return entry["value"]
                else:
                    # Expired, remove it
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 30) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl_seconds,
                "created_at": time.time()
            }
            logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
    
    def delete(self, key: str) -> bool:
        """Delete a specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern (simple prefix match)"""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            if keys_to_delete:
                logger.info(f"Cache INVALIDATE pattern '{pattern}': {len(keys_to_delete)} keys")
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED: {count} entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            now = time.time()
            active_count = sum(1 for v in self._cache.values() if v["expires_at"] > now)
            expired_count = sum(1 for v in self._cache.values() if v["expires_at"] <= now)
            return {
                "total_entries": len(self._cache),
                "active_entries": active_count,
                "expired_entries": expired_count,
                "keys": list(self._cache.keys())
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries (call periodically)"""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._cache.items() if v["expires_at"] <= now]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Cache CLEANUP: removed {len(expired_keys)} expired entries")
            return len(expired_keys)


# Global cache instance
cache = InMemoryCache()


def cached(ttl_seconds: int = 30, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl_seconds=60, key_prefix="analytics")
        def get_dashboard_data():
            return expensive_computation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{hash(args)}"
            if kwargs:
                cache_key += f":{hash(frozenset(kwargs.items()))}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator


def invalidate_dashboard_cache():
    """Invalidate all dashboard-related cache entries"""
    cache.invalidate_pattern("dashboard:")
    cache.invalidate_pattern("analytics:")
    cache.invalidate_pattern("mothers:")
    cache.invalidate_pattern("risk:")


def invalidate_mothers_cache():
    """Invalidate mothers-related cache"""
    cache.invalidate_pattern("mothers:")
    cache.invalidate_pattern("dashboard:")


def invalidate_risk_cache():
    """Invalidate risk assessment cache"""
    cache.invalidate_pattern("risk:")
    cache.invalidate_pattern("dashboard:")
    cache.invalidate_pattern("analytics:")
