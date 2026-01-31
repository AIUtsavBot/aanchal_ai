"""
Postnatal Care API Routes
Backend endpoints for postnatal care with Redis caching
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from datetime import datetime

from models.postnatal_models import (
    MotherPostnatalAssessmentCreate,
    MotherPostnatalAssessmentResponse,
    ChildHealthAssessmentCreate,
    ChildHealthAssessmentResponse,
    PostnatalMothersQuery,
    PostnatalChildrenQuery,
    PostnatalMothersResponse,
    PostnatalChildrenResponse,
    AssessmentHistoryResponse
)
from services.auth_service import supabase_admin
from routes.auth_routes import get_current_user

# Import cache service
try:
    from services.cache_service import cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/postnatal", tags=["postnatal"])


# ==================== MOTHERS ====================

@router.get("/mothers", response_model=PostnatalMothersResponse)
async def get_postnatal_mothers(
    asha_worker_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: str = Query("postnatal"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of postnatal mothers with caching
    
    - **asha_worker_id**: Filter by ASHA worker
    - **doctor_id**: Filter by doctor
    - **status**: Mother status (default: postnatal)
    - **limit**: Number of results (1-100)
    - **offset**: Pagination offset
    """
    try:
        # Build cache key
        cache_key = f"postnatal:mothers:{asha_worker_id or 'all'}:{doctor_id or 'all'}:{status}:{offset}:{limit}"
        
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"📊 Postnatal mothers served from cache")
                cached_data["cached"] = True
                return cached_data
        
        # Build query
        query = supabase_admin.table("mothers").select("*").eq("status", status)
        
        if asha_worker_id:
            query = query.eq("asha_worker_id", asha_worker_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Apply pagination - rebuild query to avoid mutation issues
        query = supabase_admin.table("mothers").select("*").eq("status", status)
        if asha_worker_id:
            query = query.eq("asha_worker_id", asha_worker_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        mothers_result = query.execute()
        mothers = mothers_result.data or []
        
        result = PostnatalMothersResponse(
            mothers=mothers,
            total=total,
            has_more=total > (offset + limit),
            cached=False
        )
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, result.dict(), ttl_seconds=30)
            logger.info(f"📊 Postnatal mothers cached for 30s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching postnatal mothers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching mothers: {str(e)}"
        )


# ==================== CHILDREN ====================

@router.get("/children", response_model=PostnatalChildrenResponse)
async def get_postnatal_children(
    mother_id: Optional[str] = Query(None),
    asha_worker_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of children with caching
    
    - **mother_id**: Filter by mother
    - **asha_worker_id**: Filter by ASHA worker (via mother)
    - **doctor_id**: Filter by doctor (via mother)
    - **limit**: Number of results (1-100)
    - **offset**: Pagination offset
    """
    try:
        # Build cache key
        cache_key = f"postnatal:children:{mother_id or 'all'}:{asha_worker_id or 'all'}:{doctor_id or 'all'}:{offset}:{limit}"
        
        # Check cache
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"📊 Children served from cache")
                cached_data["cached"] = True
                return cached_data
        
        # If filtering by asha/doctor, first get mother IDs
        mother_ids = None
        if asha_worker_id or doctor_id:
            mothers_query = supabase_admin.table("mothers").select("id").eq("status", "postnatal")
            if asha_worker_id:
                mothers_query = mothers_query.eq("asha_worker_id", asha_worker_id)
            if doctor_id:
                mothers_query = mothers_query.eq("doctor_id", doctor_id)
            
            mothers_result = mothers_query.execute()
            mother_ids = [m["id"] for m in (mothers_result.data or [])]
            
            if not mother_ids:
                return PostnatalChildrenResponse(children=[], total=0, has_more=False)
        
        # Build children query
        query = supabase_admin.table("children").select("*")
        
        if mother_id:
            query = query.eq("mother_id", mother_id)
        elif mother_ids:
            query = query.in_("mother_id", mother_ids)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Apply pagination - rebuild query to avoid mutation issues
        query = supabase_admin.table("children").select("*")
        if mother_id:
            query = query.eq("mother_id", mother_id)
        elif mother_ids:
            query = query.in_("mother_id", mother_ids)
        query = query.order("birth_date", desc=True).range(offset, offset + limit - 1)

        children_result = query.execute()
        children = children_result.data or []
        
        result = PostnatalChildrenResponse(
            children=children,
            total=total,
            has_more=total > (offset + limit),
            cached=False
        )
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, result.dict(), ttl_seconds=30)
            logger.info(f"📊 Children cached for 30s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching children: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching children: {str(e)}"
        )


# ==================== ASSESSMENTS ====================

@router.post("/assessments/mother", status_code=status.HTTP_201_CREATED)
async def create_mother_assessment(
    assessment: MotherPostnatalAssessmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a postnatal assessment for a mother
    
    Automatically invalidates related caches
    """
    try:
        # Add current user as assessor if not provided
        if not assessment.assessor_id:
            assessment.assessor_id = current_user.get("id")
        if not assessment.assessor_role:
            assessment.assessor_role = current_user.get("role", "unknown")
        
        # Convert to dict for insertion
        assessment_data = assessment.dict()
        assessment_data["assessment_type"] = "mother_postnatal"
        assessment_data["created_at"] = datetime.utcnow().isoformat()
        
        # Insert into database
        result = supabase_admin.table("postnatal_assessments").insert(assessment_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assessment"
            )
        
        # Invalidate relevant caches
        if CACHE_AVAILABLE and cache:
            cache.delete_pattern(f"postnatal:assessments:{assessment.mother_id}*")
            cache.delete_pattern(f"postnatal:mothers:*")
            logger.info(f"🔄 Invalidated postnatal caches for mother {assessment.mother_id}")
        
        logger.info(f"✅ Created mother assessment for {assessment.mother_id}")
        
        return {
            "success": True,
            "message": "Assessment created successfully",
            "assessment": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating mother assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assessment: {str(e)}"
        )


@router.post("/assessments/child", status_code=status.HTTP_201_CREATED)
async def create_child_assessment(
    assessment: ChildHealthAssessmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a health assessment for a child
    
    Automatically invalidates related caches
    """
    try:
        # Add current user as assessor if not provided
        if not assessment.assessor_id:
            assessment.assessor_id = current_user.get("id")
        if not assessment.assessor_role:
            assessment.assessor_role = current_user.get("role", "unknown")
        
        # Convert to dict for insertion
        assessment_data = assessment.dict()
        assessment_data["assessment_type"] = "child_checkup"
        assessment_data["created_at"] = datetime.utcnow().isoformat()
        
        # Insert into database
        result = supabase_admin.table("postnatal_assessments").insert(assessment_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assessment"
            )
        
        # Invalidate relevant caches
        if CACHE_AVAILABLE and cache:
            cache.delete_pattern(f"postnatal:assessments:*:{assessment.child_id}")
            cache.delete_pattern(f"postnatal:children:*")
            logger.info(f"🔄 Invalidated postnatal caches for child {assessment.child_id}")
        
        logger.info(f"✅ Created child assessment for {assessment.child_id}")
        
        return {
            "success": True,
            "message": "Assessment created successfully",
            "assessment": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating child assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assessment: {str(e)}"
        )


@router.get("/assessments/{mother_id}", response_model=AssessmentHistoryResponse)
async def get_assessment_history(
    mother_id: str,
    child_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get assessment history for a mother and/or child with caching
    
    - **mother_id**: Mother's ID
    - **child_id**: Optional child ID filter
    - **limit**: Number of assessments to return
    """
    try:
        # Build cache key
        cache_key = f"postnatal:assessments:{mother_id}:{child_id or 'all'}:{limit}"
        
        # Check cache
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"📊 Assessment history served from cache")
                cached_data["cached"] = True
                return cached_data
        
        # Build query
        query = supabase_admin.table("postnatal_assessments").select("*").eq("mother_id", mother_id)
        
        if child_id:
            query = query.eq("child_id", child_id)
        
        query = query.order("assessment_date", desc=True).limit(limit)
        
        assessments_result = query.execute()
        assessments = assessments_result.data or []
        
        # Get mother info
        mother_result = supabase_admin.table("mothers").select("*").eq("id", mother_id).single().execute()
        mother_info = mother_result.data if mother_result.data else None
        
        # Get child info if specified
        child_info = None
        if child_id:
            child_result = supabase_admin.table("children").select("*").eq("id", child_id).single().execute()
            child_info = child_result.data if child_result.data else None
        
        result = AssessmentHistoryResponse(
            assessments=assessments,
            total=len(assessments),
            mother_info=mother_info,
            child_info=child_info,
            cached=False
        )
        
        # Cache for 60 seconds
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, result.dict(), ttl_seconds=60)
            logger.info(f"📊 Assessment history cached for 60s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fetching assessment history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assessments: {str(e)}"
        )
