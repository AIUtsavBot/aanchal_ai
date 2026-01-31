"""
Aanchal AI - Hybrid Cache Service
Supports both Redis (production) and in-memory (development) caching
"""

import os
import time
import json
import threading
import logging
from typing import Any, Optional, Dict, Union
from datetime import timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class HybridCache:
    """
    Intelligent cache that uses Redis if available, falls back to in-memory
    """
    
    def __init__(self):
        self._use_redis = False
        self._redis_client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._connect_redis()
    
    def _connect_redis(self):
        """Attempt to connect to Redis"""
        redis_url = os.getenv("REDIS_URL")
        
        if not redis_url:
            logger.info("📦 Using in-memory cache (REDIS_URL not set)")
            return
        
        try:
            import redis
            from redis.exceptions import RedisError
            
            self._redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self._redis_client.ping()
            self._use_redis = True
            logger.info("✅ Redis cache connected successfully")
            
        except ImportError:
            logger.warning("⚠️  Redis package not installed, using in-memory cache")
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            logger.info("📦 Falling back to in-memory cache")
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis"""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)
    
    def _deserialize(self, value: Optional[str]) -> Any:
        """Deserialize value from Redis"""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self._use_redis and self._redis_client:
            try:
                value = self._redis_client.get(key)
                if value:
                    logger.debug(f"Redis HIT: {key}")
                    return self._deserialize(value)
                logger.debug(f"Redis MISS: {key}")
                return None
            except Exception as e:
                logger.error(f"Redis GET error: {e}, falling back to memory")
                # Don't try Redis again until reconnect
                self._use_redis = False
        
        # In-memory cache
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if time.time() < entry["expires_at"]:
                    logger.debug(f"Memory HIT: {key}")
                    return entry["value"]
                else:
                    del self._memory_cache[key]
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Union[int, timedelta, None] = 30
    ) -> bool:
        """Set value in cache with TTL"""
        if isinstance(ttl_seconds, timedelta):
            ttl_seconds = int(ttl_seconds.total_seconds())
        elif ttl_seconds is None:
            ttl_seconds = 30
        
        if self._use_redis and self._redis_client:
            try:
                serialized = self._serialize(value)
                self._redis_client.setex(key, ttl_seconds, serialized)
                logger.debug(f"Redis SET: {key} (TTL: {ttl_seconds}s)")
                return True
            except Exception as e:
                logger.error(f"Redis SET error: {e}, falling back to memory")
                self._use_redis = False
        
        # In-memory cache
        with self._lock:
            self._memory_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl_seconds,
                "created_at": time.time()
            }
            logger.debug(f"Memory SET: {key} (TTL: {ttl_seconds}s)")
            return True
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not keys:
            return 0
        
        deleted = 0
        
        if self._use_redis and self._redis_client:
            try:
                deleted = self._redis_client.delete(*keys)
                logger.debug(f"Redis DELETE: {keys} ({deleted} deleted)")
                return deleted
            except Exception as e:
                logger.error(f"Redis DELETE error: {e}")
                self._use_redis = False
        
        # In-memory cache
        with self._lock:
            for key in keys:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    deleted += 1
            logger.debug(f"Memory DELETE: {keys} ({deleted} deleted)")
        
        return deleted
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        deleted = 0
        
        if self._use_redis and self._redis_client:
            try:
                keys = list(self._redis_client.scan_iter(match=pattern))
                if keys:
                    deleted = self._redis_client.delete(*keys)
                    logger.info(f"Redis INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            except Exception as e:
                logger.error(f"Redis pattern invalidation error: {e}")
                self._use_redis = False
        
        # In-memory cache - simple prefix match
        with self._lock:
            keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
            for key in keys_to_delete:
                del self._memory_cache[key]
            deleted = len(keys_to_delete)
            if deleted > 0:
                logger.info(f"Memory INVALIDATE: {pattern} ({deleted} keys)")
        
        return deleted
    
    def clear(self) -> None:
        """Clear all cache"""
        if self._use_redis and self._redis_client:
            try:
                self._redis_client.flushdb()
                logger.warning("🗑️  Redis cache cleared!")
                return
            except Exception as e:
                logger.error(f"Redis FLUSHDB error: {e}")
        
        with self._lock:
            count = len(self._memory_cache)
            self._memory_cache.clear()
            logger.warning(f"🗑️  Memory cache cleared: {count} entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self._use_redis and self._redis_client:
            try:
                info = self._redis_client.info("stats")
                return {
                    "backend": "redis",
                    "total_keys": self._redis_client.dbsize(),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "hit_rate": (
                        info.get("keyspace_hits", 0) / 
                        (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    ) * 100
                }
            except Exception as e:
                logger.error(f"Redis INFO error: {e}")
        
        # In-memory stats
        with self._lock:
            now = time.time()
            active = sum(1 for v in self._memory_cache.values() if v["expires_at"] > now)
            return {
                "backend": "memory",
                "total_entries": len(self._memory_cache),
                "active_entries": active,
                "keys": list(self._memory_cache.keys())
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries (for in-memory cache)"""
        if self._use_redis:
            return 0  # Redis handles expiration automatically
        
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._memory_cache.items() if v["expires_at"] <= now]
            for key in expired_keys:
                del self._memory_cache[key]
            if expired_keys:
                logger.debug(f"Memory CLEANUP: removed {len(expired_keys)} expired entries")
            return len(expired_keys)


# Global cache instance
cache = HybridCache()


# Decorator for caching function results
def cached(ttl_seconds: int = 30, key_prefix: str = ""):
    """
    Cache decorator with automatic key generation
    
    Usage:
        @cached(ttl_seconds=60, key_prefix="mothers")
        async def get_mothers_list():
            return await expensive_query()
    """
    import inspect
    
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{func.__name__}"
                if args:
                    cache_key += f":{hash(args)}"
                if kwargs:
                    cache_key += f":{hash(frozenset(kwargs.items()))}"
                
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = await func(*args, **kwargs)
                cache.set(cache_key, result, ttl_seconds)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_key = f"{key_prefix}:{func.__name__}"
                if args:
                    cache_key += f":{hash(args)}"
                if kwargs:
                    cache_key += f":{hash(frozenset(kwargs.items()))}"
                
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl_seconds)
                return result
            return sync_wrapper
    
    return decorator


# Helper functions for cache invalidation
def invalidate_dashboard_cache():
    """Invalidate all dashboard-related cache"""
    cache.invalidate_pattern("dashboard:*")
    cache.invalidate_pattern("analytics:*")
    cache.invalidate_pattern("mothers:*")
    cache.invalidate_pattern("risk:*")


def invalidate_mothers_cache():
    """Invalidate mothers-related cache"""
    cache.invalidate_pattern("mothers:*")
    cache.invalidate_pattern("dashboard:*")


def invalidate_risk_cache():
    """Invalidate risk assessment cache"""
    cache.invalidate_pattern("risk:*")
    cache.invalidate_pattern("dashboard:*")
    cache.invalidate_pattern("analytics:*")


def invalidate_admin_cache():
    """Invalidate all admin panel cache keys"""
    cache.delete("admin:full")
    cache.delete("admin:doctors")
    cache.delete("admin:asha-workers")
    cache.delete("admin:mothers")
    cache.delete("admin:children")
    cache.delete("admin:stats")
    logger.info("🗑️ Admin cache invalidated")

