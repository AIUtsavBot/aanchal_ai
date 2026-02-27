"""
Postnatal Care API Routes
Backend endpoints for postnatal care with Redis caching
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from fastapi.encoders import jsonable_encoder

from models.postnatal_models import (
    MotherPostnatalAssessmentCreate,
    MotherPostnatalAssessmentResponse,
    ChildHealthAssessmentCreate,
    ChildHealthAssessmentResponse,
    PostnatalMothersQuery,
    PostnatalChildrenQuery,
    PostnatalMothersResponse,
    PostnatalChildrenResponse,
    AssessmentHistoryResponse,
    ChildCreate,
    ChildResponse,
    VaccinationCreate,
    VaccinationResponse,
    VaccinationListResponse,
    GrowthRecordCreate,
    GrowthRecordResponse,
    GrowthHistoryResponse
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
    mother_status: str = Query("postnatal", alias="status"),
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
        cache_key = f"postnatal:mothers:{asha_worker_id or 'all'}:{doctor_id or 'all'}:{mother_status}:{offset}:{limit}"
        
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"📊 Postnatal mothers served from cache")
                cached_data["cached"] = True
                return cached_data
        
        # Build query
        query = supabase_admin.table("mothers").select("*").eq("status", mother_status)
        
        if asha_worker_id:
            query = query.eq("asha_worker_id", asha_worker_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0
        
        # Apply pagination
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
            detail="Error fetching mothers. Please try again later."
        )


# ==================== CHILDREN ====================

@router.post("/children", status_code=status.HTTP_201_CREATED, response_model=ChildResponse)
async def register_child(
    child: ChildCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new child
    
    - **name**: Child's full name
    - **mother_id**: UUID of the mother
    - **birth_date**: Date of birth (YYYY-MM-DD)
    - **gender**: male, female, other
    """
    try:
        # Verify mother exists
        mother = supabase_admin.table("mothers").select("id, asha_worker_id, doctor_id").eq("id", child.mother_id).single().execute()
        if not mother.data:
            raise HTTPException(status_code=404, detail="Mother not found")
            
        # Inherit ASHA/Doctor from mother if not provided
        child_data = child.dict()
        if not child_data.get("asha_worker_id"):
            child_data["asha_worker_id"] = mother.data.get("asha_worker_id")
        if not child_data.get("doctor_id"):
            child_data["doctor_id"] = mother.data.get("doctor_id")
            
        child_data["created_at"] = datetime.utcnow().isoformat()
        
        # Insert into database
        result = supabase_admin.table("children").insert(child_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register child"
            )
            
        # Invalidate caches
        if CACHE_AVAILABLE and cache:
            cache.delete_pattern(f"postnatal:children:*")
            logger.info(f"🔄 Invalidated children cache for mother {child.mother_id}")
            
        logger.info(f"✅ Registered child {result.data[0]['id']} for mother {child.mother_id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registering child: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering child. Please try again later."
        )

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
        query = supabase_admin.table("children").select("*, mothers:mother_id(id, name, phone, asha_worker_id, doctor_id)")
        
        if mother_id:
            query = query.eq("mother_id", mother_id)
        elif mother_ids:
            query = query.in_("mother_id", mother_ids)
        
        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0
        
        # Apply pagination
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
            detail="Error fetching children. Please try again later."
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
        # Normalize assessor role for DB constraint check (asha, anm, doctor, nurse)
        raw_role = assessment.assessor_role or current_user.get("role", "unknown")
        raw_role = raw_role.lower()
        
        if raw_role == "asha_worker":
            assessment.assessor_role = "asha"
        else:
            assessment.assessor_role = raw_role
            
        # Add current user as assessor if not provided
        if not assessment.assessor_id:
            assessment.assessor_id = current_user.get("id")
        
        # Convert to dict for insertion
        # Convert to dict for insertion (and handle date serialization)
        assessment_data = jsonable_encoder(assessment.dict())
        assessment_data["assessment_type"] = "mother_postnatal"
        # Use IST (UTC+5:30)
        assessment_data["created_at"] = (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat()
        
        # Insert into database
        result = supabase_admin.table("postnatal_assessments").insert(assessment_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assessment"
            )
        
        # Invalidate relevant caches
        if CACHE_AVAILABLE and cache:
            cache.invalidate_pattern(f"postnatal:assessments:{assessment.mother_id}*")
            cache.invalidate_pattern(f"postnatal:mothers:*")
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
            detail="Error creating assessment. Please try again later."
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
        # Normalize assessor role for DB constraint check (asha, anm, doctor, nurse)
        raw_role = assessment.assessor_role or current_user.get("role", "unknown")
        raw_role = raw_role.lower()
        
        if raw_role == "asha_worker":
            assessment.assessor_role = "asha"
        else:
            assessment.assessor_role = raw_role
            
        # Add current user as assessor if not provided
        if not assessment.assessor_id:
            assessment.assessor_id = current_user.get("id")
        
        # Convert to dict for insertion
        # Convert to dict for insertion (and handle date serialization)
        assessment_data = jsonable_encoder(assessment.dict())
        
        assessment_data["assessment_type"] = "child_checkup"
        # Use IST (UTC+5:30)
        assessment_data["created_at"] = (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat()
        
        # Insert into database
        result = supabase_admin.table("postnatal_assessments").insert(assessment_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create assessment"
            )

        # Sync to Growth Records if metrics exist
        # Growth record requires weight_kg at minimum
        if assessment.weight_kg:
            try:
                # Calculate age details
                age_days = assessment.age_days or 0
                age_months = int(age_days / 30.44)  # Approximate months
                
                # Check if assessor_id is a valid UUID
                measured_by = None
                if assessment.assessor_id:
                    try:
                        import uuid
                        uuid.UUID(str(assessment.assessor_id))
                        measured_by = assessment.assessor_id
                    except ValueError:
                        # If not a valid UUID (e.g. "25"), leave as None to avoid DB error
                        logger.warning(f"⚠️ Assessor ID '{assessment.assessor_id}' is not a UUID. Leaving measured_by as None.")
                        measured_by = None

                growth_data = {
                    "child_id": assessment.child_id,
                    "measurement_date": jsonable_encoder(assessment.assessment_date),
                    "weight_kg": assessment.weight_kg,
                    "height_cm": assessment.length_cm, # Map length to height
                    "head_circumference_cm": assessment.head_circumference_cm,
                    "measured_by": measured_by,
                    "age_days": age_days,
                    "age_months": age_months, 
                    "notes": "Auto-generated from Health Assessment",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Insert growth record
                supabase_admin.table("growth_records").insert(growth_data).execute()
                logger.info(f"✅ Auto-created growth record for child {assessment.child_id}")
                
                 # Invalidate growth cache
                if CACHE_AVAILABLE and cache:
                    cache.delete(f"postnatal:growth:{assessment.child_id}:*")
                    
            except Exception as ge:
                logger.error(f"⚠️ Failed to sync growth record: {ge}")
                # We do not raise here to avoid rolling back the main assessment
        
        # Invalidate relevant caches
        if CACHE_AVAILABLE and cache:
            cache.invalidate_pattern(f"postnatal:assessments:*:{assessment.child_id}")
            cache.invalidate_pattern(f"postnatal:children:*")
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
            detail="Error creating assessment. Please try again later."
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
        
        # Sort by date AND time (latest first)
        query = query.order("assessment_date", desc=True).order("created_at", desc=True).limit(limit)
        
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
            detail="Error fetching assessment history. Please try again later."
        )
        
# ==================== VACCINATIONS ====================
# Moved to santanraksha.py

<<<<<<< HEAD
=======
@router.get("/children/{child_id}/vaccinations", response_model=VaccinationListResponse)
async def get_child_vaccinations(
    child_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get vaccination records for a child"""
    try:
        # Check cache
        cache_key = f"postnatal:vaccinations:{child_id}:{limit}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data["cached"] = True
                return cached_data
                
        # Get all vaccinations for this child
        query = supabase_admin.table("vaccinations").select("*").eq("child_id", child_id)
        
        result = query.execute()
        vaccinations = result.data or []
        
        # Calculate stats
        total = len(vaccinations)
        completed = sum(1 for v in vaccinations if v.get("status") == "completed")
        overdue = sum(1 for v in vaccinations if v.get("status") == "overdue")
        
        response = VaccinationListResponse(
            vaccinations=vaccinations,
            total=total,
            completed=completed,
            pending=total - completed,
            overdue=overdue,
            cached=False
        )
        
        # Cache
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, response.dict(), ttl_seconds=60)
            
        return response
        
    except Exception as e:
        logger.error(f"Error fetching vaccinations: {e}")
        raise HTTPException(status_code=500, detail="Error fetching vaccinations")


@router.post("/vaccinations", status_code=status.HTTP_201_CREATED, response_model=VaccinationResponse)
async def create_vaccination(
    vaccination: VaccinationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Record a vaccination (or update existing)"""
    try:
        # Filter out None values to avoid Supabase column mismatch errors
        raw_data = vaccination.dict()
        data = {k: v for k, v in raw_data.items() if v is not None}
        
        # Convert date objects to ISO strings for Supabase
        for key in list(data.keys()):
            if isinstance(data[key], date):
                data[key] = data[key].isoformat()
        
        data["created_at"] = datetime.utcnow().isoformat()
        if not data.get("administered_by"):
            data["administered_by"] = f"{current_user.get('role', 'User')} {current_user.get('id')}"
            
        # Check if record exists for this vaccine and child
        existing = supabase_admin.table("vaccinations") \
            .select("id") \
            .eq("child_id", vaccination.child_id) \
            .eq("vaccine_name", vaccination.vaccine_name) \
            .execute()
            
        res = None
        if existing.data:
            # Update
            res = supabase_admin.table("vaccinations").update(data).eq("id", existing.data[0]['id']).execute()
        else:
            # Insert
            res = supabase_admin.table("vaccinations").insert(data).execute()
            
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save vaccination")
            
        # Invalidate cache
        if CACHE_AVAILABLE and cache:
            cache.delete(f"postnatal:vaccinations:{vaccination.child_id}:*")
            
        return res.data[0]
        
    except Exception as e:
        logger.error(f"Error saving vaccination: {e}")
        raise HTTPException(status_code=500, detail="Error saving vaccination")
>>>>>>> c303068 (feat: postnatal context + vaccination fix + brain audit)


# ==================== GROWTH ====================
# Moved to santanraksha.py

<<<<<<< HEAD
=======
@router.get("/children/{child_id}/growth", response_model=GrowthHistoryResponse)
async def get_child_growth(
    child_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get growth records for a child"""
    try:
        # Check cache
        cache_key = f"postnatal:growth:{child_id}:{limit}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data["cached"] = True
                return cached_data
                
        # Get growth records
        query = supabase_admin.table("growth_records") \
            .select("*") \
            .eq("child_id", child_id) \
            .order("measurement_date", desc=True) \
            .limit(limit)
            
        result = query.execute()
        records = result.data or []
        
        # Get child info
        child_res = supabase_admin.table("children").select("*").eq("id", child_id).single().execute()
        
        response = GrowthHistoryResponse(
            records=records,
            total=len(records),
            child_info=child_res.data,
            cached=False
        )
        
        # Cache
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, response.dict(), ttl_seconds=60)
            
        return response
        
    except Exception as e:
        logger.error(f"Error fetching growth records: {e}")
        raise HTTPException(status_code=500, detail="Error fetching growth records")


@router.post("/growth", status_code=status.HTTP_201_CREATED, response_model=GrowthRecordResponse)
async def create_growth_record(
    record: GrowthRecordCreate,
    current_user: dict = Depends(get_current_user)
):
    """Record a growth measurement"""
    try:
        data = jsonable_encoder(record.dict())
        data["created_at"] = datetime.utcnow().isoformat()
        if not data.get("measured_by"):
            data["measured_by"] = f"{current_user.get('role', 'User')} {current_user.get('id')}"
            
        # Calculate Z-scores logic could go here, or handled by frontend/AI
        
        res = supabase_admin.table("growth_records").insert(data).execute()
            
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save growth record")
            
        # Invalidate cache
        if CACHE_AVAILABLE and cache:
            cache.delete(f"postnatal:growth:{record.child_id}:*")
            
        return res.data[0]
        
    except Exception as e:
        logger.error(f"Error saving growth record: {e}")
        raise HTTPException(status_code=500, detail="Error saving growth record")
>>>>>>> c303068 (feat: postnatal context + vaccination fix + brain audit)

# ==================== ASSESSMENTS ====================

@router.get("/children/{child_id}/assessments", response_model=AssessmentHistoryResponse)
async def get_child_health_assessments(
    child_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get health assessments for a child"""
    try:
        # Check cache
        cache_key = f"postnatal:assessments:{child_id}:{limit}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data["cached"] = True
                return cached_data
                
        query = supabase_admin.table("postnatal_assessments") \
            .select("*") \
            .eq("child_id", child_id) \
            .order("assessment_date", desc=True) \
            .order("created_at", desc=True) \
            .limit(limit)
            
        result = query.execute()
        assessments = result.data or []
        
        # Get child info (optional, for response completeness)
        child_res = supabase_admin.table("children").select("*").eq("id", child_id).single().execute()
        
        response = AssessmentHistoryResponse(
            success=True,
            assessments=assessments,
            total=len(assessments),
            child_info=child_res.data,
            cached=False
        )
        
        # Cache
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, response.dict(), ttl_seconds=60)
            
        return response
        
    except Exception as e:
        logger.error(f"Error fetching child assessments: {e}")
        raise HTTPException(status_code=500, detail="Error fetching child assessments")


@router.get("/mothers/{mother_id}/assessments", response_model=AssessmentHistoryResponse)
async def get_mother_health_assessments(
    mother_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get health assessments for a mother"""
    try:
        # Check cache
        cache_key = f"postnatal:assessments:mother:{mother_id}:{limit}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data["cached"] = True
                return cached_data
                
        query = supabase_admin.table("postnatal_assessments") \
            .select("*") \
            .eq("mother_id", mother_id) \
            .order("assessment_date", desc=True) \
            .order("created_at", desc=True) \
            .limit(limit)
            
        result = query.execute()
        assessments = result.data or []
        
        # Get mother info
        mother_res = supabase_admin.table("mothers").select("*").eq("id", mother_id).single().execute()
        
        response = AssessmentHistoryResponse(
            success=True,
            assessments=assessments,
            total=len(assessments),
            mother_info=mother_res.data,
            cached=False
        )
        
        # Cache
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, response.dict(), ttl_seconds=60)
            
        return response
        
    except Exception as e:
        logger.error(f"Error fetching mother assessments: {e}")
        raise HTTPException(status_code=500, detail="Error fetching mother assessments")
        

# ==================== MILESTONES ====================
# Moved to santanraksha.py


