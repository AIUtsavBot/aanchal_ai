"""
Async Database Service
High-performance async Supabase client with connection pooling and retry logic
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
QUERY_TIMEOUT = float(os.getenv("DB_QUERY_TIMEOUT", "10.0"))
CONNECT_TIMEOUT = float(os.getenv("DB_CONNECT_TIMEOUT", "5.0"))


class AsyncSupabaseError(Exception):
    """Base exception for async Supabase operations"""
    pass


class ConnectionPoolExhausted(AsyncSupabaseError):
    """Raised when connection pool is exhausted"""
    pass


class QueryTimeout(AsyncSupabaseError):
    """Raised when query times out"""
    pass


class AsyncSupabaseClient:
    """
    Async Supabase client with enterprise-grade features:
    - Connection pooling (configurable size)
    - Automatic retry with exponential backoff
    - Query timeouts
    - Request/response logging
    - Metrics collection
    """
    
    def __init__(
        self,
        url: str = None,
        key: str = None,
        pool_size: int = POOL_SIZE,
        query_timeout: float = QUERY_TIMEOUT,
        connect_timeout: float = CONNECT_TIMEOUT
    ):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        self.pool_size = pool_size
        self.query_timeout = query_timeout
        self.connect_timeout = connect_timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        
        # Metrics
        self._query_count = 0
        self._error_count = 0
        self._total_query_time = 0.0
        
        if not self.url or not self.key:
            logger.warning("⚠️  Supabase credentials not configured for async client")
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client with connection pooling"""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        base_url=f"{self.url}/rest/v1",
                        headers={
                            "apikey": self.key,
                            "Authorization": f"Bearer {self.key}",
                            "Content-Type": "application/json",
                            "Prefer": "return=representation"
                        },
                        limits=httpx.Limits(
                            max_connections=self.pool_size,
                            max_keepalive_connections=self.pool_size // 2,
                            keepalive_expiry=30.0
                        ),
                        timeout=httpx.Timeout(
                            self.query_timeout,
                            connect=self.connect_timeout
                        )
                    )
                    logger.info(f"✅ Async DB client initialized (pool_size={self.pool_size})")
        return self._client
    
    async def close(self):
        """Close the client and release connections"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("🔌 Async DB client closed")
    
    def _build_query_params(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """Build PostgREST query parameters from filters"""
        params = {}
        
        for key, value in filters.items():
            if key == "select":
                params["select"] = value
            elif key == "order":
                params["order"] = value
            elif key == "limit":
                params["limit"] = str(value)
            elif key == "offset":
                params["offset"] = str(value)
            elif "__" in key:
                # Handle operators: field__eq, field__in, field__gte, etc.
                field, op = key.rsplit("__", 1)
                if op == "eq":
                    params[field] = f"eq.{value}"
                elif op == "neq":
                    params[field] = f"neq.{value}"
                elif op == "gt":
                    params[field] = f"gt.{value}"
                elif op == "gte":
                    params[field] = f"gte.{value}"
                elif op == "lt":
                    params[field] = f"lt.{value}"
                elif op == "lte":
                    params[field] = f"lte.{value}"
                elif op == "like":
                    params[field] = f"like.{value}"
                elif op == "ilike":
                    params[field] = f"ilike.{value}"
                elif op == "in":
                    if isinstance(value, (list, tuple)):
                        params[field] = f"in.({','.join(map(str, value))})"
                    else:
                        params[field] = f"in.({value})"
                elif op == "is":
                    params[field] = f"is.{value}"
            else:
                # Default to equality
                params[key] = f"eq.{value}"
        
        return params
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def select(
        self,
        table: str,
        columns: str = "*",
        single: bool = False,
        **filters
    ) -> Union[List[Dict], Dict, None]:
        """
        Async SELECT query with retry logic
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            single: Return single record instead of list
            **filters: Query filters (field__eq=value, field__in=[...], etc.)
        
        Returns:
            List of records or single record if single=True
        """
        start_time = datetime.now()
        
        try:
            client = await self.get_client()
            
            params = self._build_query_params(filters)
            params["select"] = columns
            
            response = await client.get(f"/{table}", params=params)
            response.raise_for_status()
            
            data = response.json()
            self._query_count += 1
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._total_query_time += elapsed
            
            if elapsed > 100:
                logger.warning(f"⚠️  Slow query: {table} took {elapsed:.0f}ms")
            else:
                logger.debug(f"📊 SELECT {table}: {len(data) if isinstance(data, list) else 1} rows in {elapsed:.0f}ms")
            
            if single:
                return data[0] if data else None
            return data
            
        except httpx.TimeoutException as e:
            self._error_count += 1
            logger.error(f"❌ Query timeout on {table}: {e}")
            raise QueryTimeout(f"Query to {table} timed out after {self.query_timeout}s")
        except httpx.HTTPStatusError as e:
            self._error_count += 1
            logger.error(f"❌ HTTP error on {table}: {e.response.status_code}")
            raise AsyncSupabaseError(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Query error on {table}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def insert(
        self,
        table: str,
        data: Union[Dict, List[Dict]],
        upsert: bool = False
    ) -> Union[Dict, List[Dict]]:
        """
        Async INSERT query with retry logic
        
        Args:
            table: Table name
            data: Record(s) to insert
            upsert: If True, update on conflict
        
        Returns:
            Inserted record(s)
        """
        start_time = datetime.now()
        
        try:
            client = await self.get_client()
            
            headers = {}
            if upsert:
                headers["Prefer"] = "resolution=merge-duplicates,return=representation"
            
            response = await client.post(f"/{table}", json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self._query_count += 1
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._total_query_time += elapsed
            
            logger.debug(f"📊 INSERT {table}: {len(result) if isinstance(result, list) else 1} rows in {elapsed:.0f}ms")
            
            return result
            
        except httpx.HTTPStatusError as e:
            self._error_count += 1
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"❌ Insert error on {table}: {error_detail}")
            raise AsyncSupabaseError(f"Insert failed: {error_detail}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Insert error on {table}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def update(
        self,
        table: str,
        data: Dict,
        **filters
    ) -> List[Dict]:
        """
        Async UPDATE query with retry logic
        
        Args:
            table: Table name
            data: Fields to update
            **filters: Query filters
        
        Returns:
            Updated record(s)
        """
        start_time = datetime.now()
        
        try:
            client = await self.get_client()
            
            params = self._build_query_params(filters)
            
            response = await client.patch(f"/{table}", json=data, params=params)
            response.raise_for_status()
            
            result = response.json()
            self._query_count += 1
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._total_query_time += elapsed
            
            logger.debug(f"📊 UPDATE {table}: {len(result) if isinstance(result, list) else 1} rows in {elapsed:.0f}ms")
            
            return result
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Update error on {table}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def delete(
        self,
        table: str,
        **filters
    ) -> List[Dict]:
        """
        Async DELETE query with retry logic
        
        Args:
            table: Table name
            **filters: Query filters (required)
        
        Returns:
            Deleted record(s)
        """
        if not filters:
            raise AsyncSupabaseError("DELETE requires at least one filter to prevent accidental data loss")
        
        start_time = datetime.now()
        
        try:
            client = await self.get_client()
            
            params = self._build_query_params(filters)
            
            response = await client.delete(f"/{table}", params=params)
            response.raise_for_status()
            
            result = response.json()
            self._query_count += 1
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._total_query_time += elapsed
            
            logger.debug(f"📊 DELETE {table}: {len(result) if isinstance(result, list) else 1} rows in {elapsed:.0f}ms")
            
            return result
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Delete error on {table}: {e}")
            raise
    
    async def count(self, table: str, **filters) -> int:
        """Get count of records matching filters"""
        try:
            client = await self.get_client()
            
            params = self._build_query_params(filters)
            headers = {"Prefer": "count=exact"}
            
            response = await client.head(f"/{table}", params=params, headers=headers)
            
            count_range = response.headers.get("content-range", "")
            if "/" in count_range:
                return int(count_range.split("/")[1])
            return 0
            
        except Exception as e:
            logger.error(f"❌ Count error on {table}: {e}")
            return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        avg_query_time = (
            self._total_query_time / self._query_count
            if self._query_count > 0 else 0
        )
        
        return {
            "total_queries": self._query_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._query_count, 1) * 100,
            "avg_query_time_ms": round(avg_query_time, 2),
            "pool_size": self.pool_size,
            "query_timeout": self.query_timeout
        }


# ==================== PARALLEL QUERY HELPERS ====================

async def parallel_queries(*queries) -> List[Any]:
    """
    Execute multiple queries in parallel using asyncio.gather
    
    Usage:
        mothers, children, assessments = await parallel_queries(
            async_db.select("mothers", status__eq="postnatal"),
            async_db.select("children"),
            async_db.select("risk_assessments")
        )
    """
    return await asyncio.gather(*queries, return_exceptions=True)


async def parallel_select(async_db: AsyncSupabaseClient, tables: List[str], **common_filters) -> Dict[str, List]:
    """
    Select from multiple tables in parallel with common filters
    
    Usage:
        data = await parallel_select(async_db, ["mothers", "children"], asha_worker_id__eq=1)
        # data = {"mothers": [...], "children": [...]}
    """
    queries = [async_db.select(table, **common_filters) for table in tables]
    results = await asyncio.gather(*queries, return_exceptions=True)
    
    return {
        table: result if not isinstance(result, Exception) else []
        for table, result in zip(tables, results)
    }


# ==================== SINGLETON INSTANCE ====================

# Global async database client
async_db = AsyncSupabaseClient()


# ==================== CONTEXT MANAGER ====================

class AsyncDB:
    """Context manager for async database operations"""
    
    def __init__(self):
        self.client = async_db
    
    async def __aenter__(self):
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't close the singleton client
        pass


# Export convenience function
def get_async_db() -> AsyncSupabaseClient:
    """Get the async database client singleton"""
    return async_db
