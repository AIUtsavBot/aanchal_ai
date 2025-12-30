"""
MatruRaksha AI - Admin Routes
Admin-only endpoints for managing doctors, ASHA workers, mothers, and assignments
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from services.auth_service import supabase_admin
from routes.auth_routes import get_current_user, require_admin
from services.email_service import send_alert_email

# Import cache service
try:
    from services.cache_service import cache, invalidate_dashboard_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache = None
    def invalidate_dashboard_cache(): pass

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])



# ==================== Pydantic Models ====================

class UpdateDoctorRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    assigned_area: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateAshaWorkerRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    assigned_area: Optional[str] = None
    is_active: Optional[bool] = None


class AssignAshaRequest(BaseModel):
    asha_worker_id: Optional[int] = None


class AssignDoctorRequest(BaseModel):
    doctor_id: Optional[int] = None


# ==================== Stats ====================

@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):
    """Get dashboard statistics - OPTIMIZED with caching"""
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("admin:stats")
            if cached_data:
                logger.debug("📊 Admin stats served from cache")
                return cached_data
        
        # Get counts efficiently
        mothers = supabase_admin.table("mothers").select("id", count="exact").execute()
        doctors = supabase_admin.table("doctors").select("id", count="exact").execute()
        asha_workers = supabase_admin.table("asha_workers").select("id", count="exact").execute()
        pending_users = supabase_admin.table("user_profiles").select("id", count="exact").is_("role", "null").execute()
        
        result = {
            "success": True,
            "stats": {
                "total_mothers": mothers.count or 0,
                "total_doctors": doctors.count or 0,
                "total_asha_workers": asha_workers.count or 0,
                "pending_approvals": pending_users.count or 0
            }
        }
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("admin:stats", result, ttl_seconds=30)
        
        return result
    except Exception as e:
        logger.error(f"❌ Get admin stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full")
async def get_admin_full_data(current_user: dict = Depends(require_admin)):
    """
    COMBINED ADMIN ENDPOINT - Returns all admin data in a single request
    Reduces frontend from 4 API calls to 1
    """
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("admin:full")
            if cached_data:
                logger.debug("📊 Admin full data served from cache")
                cached_data["cached"] = True
                return cached_data
        
        # Fetch all data in parallel (all queries at once)
        mothers_result = supabase_admin.table("mothers").select("id,name,phone,age,location,doctor_id,asha_worker_id").order("name").execute()
        doctors_result = supabase_admin.table("doctors").select("*").order("name").execute()
        asha_result = supabase_admin.table("asha_workers").select("*").order("name").execute()
        pending_users = supabase_admin.table("user_profiles").select("id", count="exact").is_("role", "null").execute()
        
        mothers = mothers_result.data or []
        doctors = doctors_result.data or []
        asha_workers = asha_result.data or []
        
        # Create lookup maps for names
        doctors_map = {d["id"]: d for d in doctors}
        asha_map = {a["id"]: a for a in asha_workers}
        
        # Count mothers per doctor/asha in memory (avoiding N+1)
        doctor_counts = {}
        asha_counts = {}
        for mother in mothers:
            if mother.get("doctor_id"):
                doctor_counts[mother["doctor_id"]] = doctor_counts.get(mother["doctor_id"], 0) + 1
            if mother.get("asha_worker_id"):
                asha_counts[mother["asha_worker_id"]] = asha_counts.get(mother["asha_worker_id"], 0) + 1
        
        # Add counts to doctors/asha workers
        for doc in doctors:
            doc["mothers_count"] = doctor_counts.get(doc["id"], 0)
        for asha in asha_workers:
            asha["mothers_count"] = asha_counts.get(asha["id"], 0)
        
        # Add names to mothers
        for mother in mothers:
            mother["doctor_name"] = doctors_map.get(mother.get("doctor_id"), {}).get("name", "Unassigned")
            mother["asha_worker_name"] = asha_map.get(mother.get("asha_worker_id"), {}).get("name", "Unassigned")
        
        result = {
            "success": True,
            "data": {
                "stats": {
                    "total_mothers": len(mothers),
                    "total_doctors": len(doctors),
                    "total_asha_workers": len(asha_workers),
                    "pending_approvals": pending_users.count or 0
                },
                "doctors": doctors,
                "asha_workers": asha_workers,
                "mothers": mothers
            },
            "cached": False
        }
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("admin:full", result, ttl_seconds=30)
            logger.info("📊 Admin full data cached for 30s")
        
        return result
    except Exception as e:
        logger.error(f"❌ Get admin full data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Doctors ====================

@router.get("/doctors")
async def list_doctors(current_user: dict = Depends(require_admin)):
    """List all doctors with assigned mothers count - OPTIMIZED"""
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("admin:doctors")
            if cached_data:
                return cached_data
        
        # Get all doctors
        doctors_result = supabase_admin.table("doctors").select("*").order("name").execute()
        doctors = doctors_result.data or []
        
        # Get ALL mothers with doctor_id in ONE query (avoid N+1)
        mothers_result = supabase_admin.table("mothers").select("doctor_id").execute()
        
        # Count in memory
        doctor_counts = {}
        for m in (mothers_result.data or []):
            did = m.get("doctor_id")
            if did:
                doctor_counts[did] = doctor_counts.get(did, 0) + 1
        
        # Add counts to doctors
        for doc in doctors:
            doc["mothers_count"] = doctor_counts.get(doc["id"], 0)
        
        result = {"success": True, "doctors": doctors}
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("admin:doctors", result, ttl_seconds=30)
        
        return result
    except Exception as e:
        logger.error(f"❌ List doctors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/doctors/{doctor_id}")
async def get_doctor_details(doctor_id: int, current_user: dict = Depends(require_admin)):
    """Get doctor details with assigned mothers"""
    try:
        # Get doctor
        doctor_result = supabase_admin.table("doctors").select("*").eq("id", doctor_id).single().execute()
        if not doctor_result.data:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        doctor = doctor_result.data
        
        # Get assigned mothers
        mothers = supabase_admin.table("mothers").select("*").eq("doctor_id", doctor_id).execute()
        doctor["assigned_mothers"] = mothers.data or []
        
        return {"success": True, "doctor": doctor}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get doctor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/doctors/{doctor_id}")
async def update_doctor(doctor_id: int, body: UpdateDoctorRequest, current_user: dict = Depends(require_admin)):
    """Update doctor information"""
    try:
        update_data = {k: v for k, v in body.dict().items() if v is not None}
        if not update_data:
            return {"success": True, "message": "No changes to update"}
        
        result = supabase_admin.table("doctors").update(update_data).eq("id", doctor_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        logger.info(f"✅ Updated doctor {doctor_id}")
        return {"success": True, "doctor": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update doctor error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: int, current_user: dict = Depends(require_admin)):
    """Delete a doctor (unassigns all mothers first)"""
    try:
        # First unassign all mothers from this doctor
        supabase_admin.table("mothers").update({"doctor_id": None}).eq("doctor_id", doctor_id).execute()
        
        # Then delete the doctor
        result = supabase_admin.table("doctors").delete().eq("id", doctor_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        logger.info(f"✅ Deleted doctor {doctor_id}")
        return {"success": True, "message": "Doctor deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete doctor error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ASHA Workers ====================

@router.get("/asha-workers")
async def list_asha_workers(current_user: dict = Depends(require_admin)):
    """List all ASHA workers with assigned mothers count - OPTIMIZED"""
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("admin:asha_workers")
            if cached_data:
                return cached_data
        
        # Get all ASHA workers
        asha_result = supabase_admin.table("asha_workers").select("*").order("name").execute()
        asha_workers = asha_result.data or []
        
        # Get ALL mothers with asha_worker_id in ONE query (avoid N+1)
        mothers_result = supabase_admin.table("mothers").select("asha_worker_id").execute()
        
        # Count in memory
        asha_counts = {}
        for m in (mothers_result.data or []):
            aid = m.get("asha_worker_id")
            if aid:
                asha_counts[aid] = asha_counts.get(aid, 0) + 1
        
        # Add counts
        for asha in asha_workers:
            asha["mothers_count"] = asha_counts.get(asha["id"], 0)
        
        result = {"success": True, "asha_workers": asha_workers}
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("admin:asha_workers", result, ttl_seconds=30)
        
        return result
    except Exception as e:
        logger.error(f"❌ List ASHA workers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/asha-workers/{asha_id}")
async def get_asha_worker_details(asha_id: int, current_user: dict = Depends(require_admin)):
    """Get ASHA worker details with assigned mothers"""
    try:
        # Get ASHA worker
        asha_result = supabase_admin.table("asha_workers").select("*").eq("id", asha_id).single().execute()
        if not asha_result.data:
            raise HTTPException(status_code=404, detail="ASHA worker not found")
        
        asha = asha_result.data
        
        # Get assigned mothers
        mothers = supabase_admin.table("mothers").select("*").eq("asha_worker_id", asha_id).execute()
        asha["assigned_mothers"] = mothers.data or []
        
        return {"success": True, "asha_worker": asha}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get ASHA worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/asha-workers/{asha_id}")
async def update_asha_worker(asha_id: int, body: UpdateAshaWorkerRequest, current_user: dict = Depends(require_admin)):
    """Update ASHA worker information"""
    try:
        update_data = {k: v for k, v in body.dict().items() if v is not None}
        if not update_data:
            return {"success": True, "message": "No changes to update"}
        
        result = supabase_admin.table("asha_workers").update(update_data).eq("id", asha_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="ASHA worker not found")
        
        logger.info(f"✅ Updated ASHA worker {asha_id}")
        return {"success": True, "asha_worker": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update ASHA worker error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/asha-workers/{asha_id}")
async def delete_asha_worker(asha_id: int, current_user: dict = Depends(require_admin)):
    """Delete an ASHA worker (unassigns all mothers first)"""
    try:
        # First unassign all mothers from this ASHA worker
        supabase_admin.table("mothers").update({"asha_worker_id": None}).eq("asha_worker_id", asha_id).execute()
        
        # Then delete the ASHA worker
        result = supabase_admin.table("asha_workers").delete().eq("id", asha_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="ASHA worker not found")
        
        logger.info(f"✅ Deleted ASHA worker {asha_id}")
        return {"success": True, "message": "ASHA worker deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete ASHA worker error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Mothers ====================

@router.get("/mothers")
async def list_mothers(current_user: dict = Depends(require_admin)):
    """List all mothers with their assignments - OPTIMIZED"""
    try:
        # Check cache first
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get("admin:mothers")
            if cached_data:
                return cached_data
        
        # Get all mothers with doctor and ASHA worker info
        mothers_result = supabase_admin.table("mothers").select("*").order("name").execute()
        mothers = mothers_result.data or []
        
        # Get doctor and ASHA worker names for each mother
        doctors = {d["id"]: d for d in (supabase_admin.table("doctors").select("id, name").execute().data or [])}
        asha_workers = {a["id"]: a for a in (supabase_admin.table("asha_workers").select("id, name").execute().data or [])}
        
        for mother in mothers:
            mother["doctor_name"] = doctors.get(mother.get("doctor_id"), {}).get("name", "Unassigned")
            mother["asha_worker_name"] = asha_workers.get(mother.get("asha_worker_id"), {}).get("name", "Unassigned")
        
        result = {"success": True, "mothers": mothers}
        
        # Cache for 30 seconds
        if CACHE_AVAILABLE and cache:
            cache.set("admin:mothers", result, ttl_seconds=30)
        
        return result
    except Exception as e:
        logger.error(f"❌ List mothers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/mothers/{mother_id}/assign-asha")
async def assign_mother_to_asha(mother_id: str, body: AssignAshaRequest, current_user: dict = Depends(require_admin)):
    """Assign a mother to an ASHA worker"""
    try:
        result = supabase_admin.table("mothers").update({
            "asha_worker_id": body.asha_worker_id
        }).eq("id", mother_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        logger.info(f"✅ Assigned mother {mother_id} to ASHA worker {body.asha_worker_id}")
        return {"success": True, "message": "Assignment updated", "mother": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Assign ASHA error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mothers/{mother_id}/assign-doctor")
async def assign_mother_to_doctor(mother_id: str, body: AssignDoctorRequest, current_user: dict = Depends(require_admin)):
    """Assign a mother to a doctor"""
    try:
        result = supabase_admin.table("mothers").update({
            "doctor_id": body.doctor_id
        }).eq("id", mother_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        logger.info(f"✅ Assigned mother {mother_id} to doctor {body.doctor_id}")
        return {"success": True, "message": "Assignment updated", "mother": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Assign doctor error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Email Alerts ====================

class SendAlertRequest(BaseModel):
    alert_type: str = "emergency"
    message: Optional[str] = None


@router.post("/mothers/{mother_id}/send-alert")
async def send_mother_alert(mother_id: str, body: SendAlertRequest, current_user: dict = Depends(require_admin)):
    """Send email alerts to assigned doctor and ASHA worker for a mother"""
    try:
        # Get mother details
        mother_result = supabase_admin.table("mothers").select("*").eq("id", mother_id).single().execute()
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother = mother_result.data
        sent_to = []
        
        # Get ASHA worker details
        if mother.get("asha_worker_id"):
            asha_result = supabase_admin.table("asha_workers").select("*").eq("id", mother["asha_worker_id"]).single().execute()
            if asha_result.data and asha_result.data.get("email"):
                asha = asha_result.data
                result = send_alert_email(
                    to_email=asha["email"],
                    recipient_name=asha.get("name", "ASHA Worker"),
                    recipient_role="ASHA Worker",
                    mother_name=mother.get("name", "Mother"),
                    mother_id=str(mother_id),
                    mother_phone=mother.get("phone", ""),
                    location=mother.get("location", ""),
                    alert_type=body.alert_type
                )
                if result.get("status") == "sent":
                    sent_to.append(f"ASHA: {asha.get('name')} ({asha['email']})")
                    logger.info(f"✅ Alert email sent to ASHA: {asha['email']}")
        
        # Get Doctor details
        if mother.get("doctor_id"):
            doctor_result = supabase_admin.table("doctors").select("*").eq("id", mother["doctor_id"]).single().execute()
            if doctor_result.data and doctor_result.data.get("email"):
                doctor = doctor_result.data
                result = send_alert_email(
                    to_email=doctor["email"],
                    recipient_name=doctor.get("name", "Doctor"),
                    recipient_role="Doctor",
                    mother_name=mother.get("name", "Mother"),
                    mother_id=str(mother_id),
                    mother_phone=mother.get("phone", ""),
                    location=mother.get("location", ""),
                    alert_type=body.alert_type
                )
                if result.get("status") == "sent":
                    sent_to.append(f"Doctor: {doctor.get('name')} ({doctor['email']})")
                    logger.info(f"✅ Alert email sent to Doctor: {doctor['email']}")
        
        if sent_to:
            return {"success": True, "message": f"Alerts sent to: {', '.join(sent_to)}", "sent_to": sent_to}
        else:
            return {"success": False, "message": "No email addresses configured for assigned contacts", "sent_to": []}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Send alert error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
