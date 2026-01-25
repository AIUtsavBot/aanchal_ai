"""
MatruRaksha - Pagination Utilities
Helper functions for paginated API responses
"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field
from fastapi import Query

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    limit: int = Field(50, ge=1, le=100, description="Number of items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")
    
    @property
    def skip(self) -> int:
        return self.offset
    
    @property
    def page(self) -> int:
        return (self.offset // self.limit) + 1


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    data: List[T]
    total: Optional[int] = None
    limit: int
    offset: int
    has_more: bool
    
    @property
    def page(self) -> int:
        return (self.offset // self.limit) + 1
    
    @property
    def page_count(self) -> Optional[int]:
        if self.total is None:
            return None
        return (self.total + self.limit - 1) // self.limit


def create_pagination_params(
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip")
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters
    
    Usage:
        @app.get("/items")
        async def get_items(pagination: PaginationParams = Depends(create_pagination_params)):
            ...
    """
    return PaginationParams(limit=limit, offset=offset)


def paginate_query(query, pagination: PaginationParams):
    """
    Apply pagination to a Supabase query
    
    Args:
        query: Supabase query builder
        pagination: Pagination parameters
    
    Returns:
        Query with range applied
    """
    start = pagination.offset
    end = pagination.offset + pagination.limit - 1
    return query.range(start, end)


def create_paginated_response(
    data: List[T],
    pagination: PaginationParams,
    total: Optional[int] = None
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response
    
    Args:
        data: List of items for current page
        pagination: Pagination parameters used
        total: Total count of items (optional)
    
    Returns:
        PaginatedResponse with metadata
    """
    return PaginatedResponse(
        data=data,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
        has_more=len(data) == pagination.limit
    )


async def get_paginated_data(
    supabase_client,
    table: str,
    pagination: PaginationParams,
    filters: Optional[dict] = None,
    order_by: Optional[str] = None,
    order_desc: bool = True
):
    """
    Generic function to get paginated data from Supabase
    
    Args:
        supabase_client: Supabase client instance
        table: Table name
        pagination: Pagination parameters
        filters: Dictionary of column:value filters
        order_by: Column to order by
        order_desc: Order descending if True
    
    Returns:
        PaginatedResponse with data
    """
    # Build query
    query = supabase_client.table(table).select("*")
    
    # Apply filters
    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)
    
    # Apply ordering
    if order_by:
        query = query.order(order_by, desc=order_desc)
    
    # Get total count (for pagination metadata)
    count_query = supabase_client.table(table).select("*", count="exact")
    if filters:
        for column, value in filters.items():
            count_query = count_query.eq(column, value)
    count_result = count_query.execute()
    total = count_result.count if hasattr(count_result, 'count') else None
    
    # Apply pagination
    query = paginate_query(query, pagination)
    
    # Execute
    result = query.execute()
    
    return create_paginated_response(
        data=result.data,
        pagination=pagination,
        total=total
    )
