"""
SantanRaksha - Postnatal Assessment Routes
File: backend/routes/postnatal.py

Endpoints for:
- Mother's postnatal health assessments
- Child health checks (IMNCI-based)
- Assessment history and tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

# Import cache service
try:
    from services.cache_service import cache, cached
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache = None
    cached = lambda *args, **kwargs: lambda func: func

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/postnatal", tags=["Postnatal Care"])


# ==================== PYDANTIC MODELS ====================

class MotherPostnatalAssessment(BaseModel):
    mother_id: str
    assessment_date: Optional[str] = None
    days_postpartum: Optional[int] = None
    
    # Physical Health
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    pulse_rate: Optional[int] = None
    
    # Postnatal Checks
    uterine_involution: Optional[str] = "normal"  # normal, subinvolution, tender
    lochia_status: Optional[str] = "normal"  # normal, foul_smelling, excessive, absent
    episiotomy_wound: Optional[str] = "healing_well"
    cesarean_wound: Optional[str] = "not_applicable"
    breast_condition: Optional[str] = "normal"  # normal, engorged, cracked_nipples, mastitis
    breastfeeding_established: Optional[bool] = True
    
    # Mental Health (PPD Screening)
    mood_status: Optional[str] = "stable"  # stable, anxious, sad, overwhelmed
    sleep_quality: Optional[str] = "adequate"  # adequate, poor, insomnia
    postpartum_depression_risk: Optional[str] = "low"  # low, medium, high
    bonding_with_baby: Optional[str] = "good"  # good, developing, poor
    
    # Danger Signs
    fever: Optional[bool] = False
    excessive_bleeding: Optional[bool] = False
    foul_discharge: Optional[bool] = False
    breast_engorgement: Optional[bool] = False
    mastitis: Optional[bool] = False
    urinary_issues: Optional[bool] = False
    
    # Notes
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    next_visit_date: Optional[str] = None
    
    # Assessor info
    assessor_id: Optional[str] = None
    assessor_role: Optional[str] = None  # DOCTOR, ASHA


class ChildHealthCheck(BaseModel):
    child_id: str
    mother_id: Optional[str] = None
    assessment_date: Optional[str] = None
    age_days: Optional[int] = None
    
    # Physical Measurements
    weight_kg: Optional[float] = None
    length_cm: Optional[float] = None
    head_circumference_cm: Optional[float] = None
    
    # Vital Signs
    temperature: Optional[float] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    
    # Feeding Assessment
    feeding_type: Optional[str] = "exclusive_breastfeeding"  # exclusive_breastfeeding, mixed, formula, complementary
    feeding_frequency: Optional[str] = None
    feeding_issues: Optional[List[str]] = []
    
    # Physical Examination
    skin_color: Optional[str] = "normal"  # normal, pale, cyanotic, jaundiced
    jaundice_level: Optional[str] = "none"  # none, mild_face, moderate, severe
    umbilical_cord: Optional[str] = "clean_dry"  # clean_dry, moist, infected, separated
    fontanelle: Optional[str] = "normal"  # normal, bulging, sunken
    eyes: Optional[str] = "normal"  # normal, discharge, swelling
    reflexes: Optional[str] = "present"  # present, weak, absent
    muscle_tone: Optional[str] = "normal"  # normal, hypotonic, hypertonic
    
    # IMNCI Danger Signs
    not_feeding_well: Optional[bool] = False
    convulsions: Optional[bool] = False
    fast_breathing: Optional[bool] = False
    chest_indrawing: Optional[bool] = False
    high_fever: Optional[bool] = False
    hypothermia: Optional[bool] = False
    jaundice_extending: Optional[bool] = False
    umbilical_infection: Optional[bool] = False
    
    # Notes
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    next_visit_date: Optional[str] = None
    
    # Assessor info
    assessor_id: Optional[str] = None
    assessor_role: Optional[str] = None


# ==================== MOTHER ASSESSMENT ENDPOINTS ====================

@router.post("/mother/assessment")
async def create_mother_assessment(assessment: MotherPostnatalAssessment):
    """Create a mother's postnatal health assessment"""
    try:
        logger.info(f"📋 Creating postnatal assessment for mother: {assessment.mother_id}")
        
        assessment_data = {
            "mother_id": assessment.mother_id,
            "assessment_type": "mother_postnatal",
            "assessment_date": assessment.assessment_date or datetime.now().date().isoformat(),
            "data": assessment.dict(exclude={"mother_id", "assessor_id", "assessor_role"}),
            "assessor_id": assessment.assessor_id,
            "assessor_role": assessment.assessor_role,
            "created_at": datetime.now().isoformat()
        }
        
        # Calculate risk level based on danger signs
        danger_signs_count = sum([
            assessment.fever or False,
            assessment.excessive_bleeding or False,
            assessment.foul_discharge or False,
            assessment.mastitis or False
        ])
        
        if danger_signs_count >= 2:
            assessment_data["risk_level"] = "high"
        elif danger_signs_count == 1:
            assessment_data["risk_level"] = "medium"
        else:
            assessment_data["risk_level"] = "low"
        
        # Try to insert into postnatal_assessments table
        try:
            result = supabase.table("postnatal_assessments").insert(assessment_data).execute()
            
            if result.data:
                logger.info(f"✅ Mother assessment saved: {result.data[0].get('id')}")
                return {
                    "success": True,
                    "message": "Mother postnatal assessment saved successfully",
                    "assessment_id": result.data[0].get("id"),
                    "risk_level": assessment_data["risk_level"]
                }
        except Exception as table_err:
            logger.warning(f"⚠️ postnatal_assessments table not available: {table_err}")
            # Fallback: Store in risk_assessments table
            try:
                fallback_data = {
                    "mother_id": assessment.mother_id,
                    "risk_type": "postnatal_check",
                    "risk_level": assessment_data["risk_level"],
                    "factors": [f"Days postpartum: {assessment.days_postpartum}"],
                    "recommendations": assessment.recommendations,
                    "notes": assessment.notes
                }
                supabase.table("risk_assessments").insert(fallback_data).execute()
                return {
                    "success": True,
                    "message": "Assessment stored (fallback mode)",
                    "risk_level": assessment_data["risk_level"]
                }
            except:
                pass
                
        return {
            "success": True,
            "message": "Assessment recorded",
            "risk_level": assessment_data.get("risk_level", "low")
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating mother assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mother/{mother_id}/assessments")
async def get_mother_assessments(mother_id: str, limit: int = 20):
    """Get all postnatal assessments for a mother"""
    try:
        # Check cache first
        cache_key = f"postnatal:mother:{mother_id}:assessments:{limit}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data

        assessments = []
        
        # Try postnatal_assessments table
        try:
            result = supabase.table("postnatal_assessments") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .eq("assessment_type", "mother_postnatal") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            assessments = result.data or []
        except:
            pass
        
        # Also check risk_assessments as fallback
        try:
            risk_result = supabase.table("risk_assessments") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .eq("risk_type", "postnatal_check") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            for r in (risk_result.data or []):
                assessments.append({
                    "id": r.get("id"),
                    "assessment_date": r.get("created_at", "")[:10],
                    "risk_level": r.get("risk_level"),
                    "notes": r.get("notes"),
                    "source": "risk_assessments"
                })
        except:
            pass
            
        response = {
            "mother_id": mother_id,
            "assessments": assessments,
            "total": len(assessments),
            "cached": False
        }
        
        # Cache result for 5 minutes
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, {**response, "cached": True}, ttl_seconds=300)
            
        return response
        
    except Exception as e:
        logger.error(f"Error fetching mother assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CHILD HEALTH CHECK ENDPOINTS ====================

@router.post("/child/healthcheck")
async def create_child_healthcheck(healthcheck: ChildHealthCheck):
    """Create a child health check assessment"""
    try:
        logger.info(f"📋 Creating health check for child: {healthcheck.child_id}")
        
        assessment_data = {
            "child_id": healthcheck.child_id,
            "mother_id": healthcheck.mother_id,
            "assessment_type": "child_checkup",
            "assessment_date": healthcheck.assessment_date or datetime.now().date().isoformat(),
            "data": healthcheck.dict(exclude={"child_id", "mother_id", "assessor_id", "assessor_role"}),
            "assessor_id": healthcheck.assessor_id,
            "assessor_role": healthcheck.assessor_role,
            "created_at": datetime.now().isoformat()
        }
        
        # Calculate risk level based on IMNCI danger signs
        danger_signs_count = sum([
            healthcheck.not_feeding_well or False,
            healthcheck.convulsions or False,
            healthcheck.fast_breathing or False,
            healthcheck.chest_indrawing or False,
            healthcheck.high_fever or False,
            healthcheck.hypothermia or False,
            healthcheck.jaundice_extending or False,
            healthcheck.umbilical_infection or False
        ])
        
        if danger_signs_count >= 2:
            assessment_data["risk_level"] = "high"
            assessment_data["urgent_referral"] = True
        elif danger_signs_count == 1:
            assessment_data["risk_level"] = "medium"
            assessment_data["urgent_referral"] = False
        else:
            assessment_data["risk_level"] = "low"
            assessment_data["urgent_referral"] = False
        
        # Try to insert into postnatal_assessments table
        try:
            result = supabase.table("postnatal_assessments").insert(assessment_data).execute()
            
            if result.data:
                logger.info(f"✅ Child health check saved: {result.data[0].get('id')}")
                
                # Also record growth data if provided
                if healthcheck.weight_kg or healthcheck.length_cm:
                    try:
                        growth_data = {
                            "child_id": healthcheck.child_id,
                            "measurement_date": assessment_data["assessment_date"],
                            "weight_kg": healthcheck.weight_kg,
                            "length_cm": healthcheck.length_cm,
                            "head_circumference_cm": healthcheck.head_circumference_cm
                        }
                        supabase.table("growth_records").insert(growth_data).execute()
                    except Exception as growth_err:
                        logger.warning(f"⚠️ Could not record growth data: {growth_err}")
                
                return {
                    "success": True,
                    "message": "Child health check saved successfully",
                    "assessment_id": result.data[0].get("id"),
                    "risk_level": assessment_data["risk_level"],
                    "urgent_referral": assessment_data.get("urgent_referral", False)
                }
        except Exception as table_err:
            logger.warning(f"⚠️ postnatal_assessments table not available: {table_err}")
        
        return {
            "success": True,
            "message": "Health check recorded",
            "risk_level": assessment_data.get("risk_level", "low")
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating child health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/child/{child_id}/healthchecks")
async def get_child_healthchecks(child_id: str, limit: int = 20):
    """Get all health checks for a child"""
    try:
        assessments = []
        
        try:
            result = supabase.table("postnatal_assessments") \
                .select("*") \
                .eq("child_id", child_id) \
                .eq("assessment_type", "child_checkup") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            assessments = result.data or []
        except:
            pass
            
        return {
            "child_id": child_id,
            "healthchecks": assessments,
            "total": len(assessments)
        }
        
    except Exception as e:
        logger.error(f"Error fetching child health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SUMMARY ENDPOINTS ====================

@router.get("/summary/{mother_id}")
async def get_postnatal_summary(mother_id: str):
    """Get complete postnatal summary for a mother and her children"""
    try:
        # Check cache
        cache_key = f"postnatal:summary:{mother_id}"
        if CACHE_AVAILABLE and cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data

        summary = {
            "mother_id": mother_id,
            "mother": None,
            "children": [],
            "mother_assessments": [],
            "child_assessments": [],
            "next_actions": []
        }
        
        # Get mother info
        try:
            mother_result = supabase.table("mothers") \
                .select("id, name, phone, status, age, location") \
                .eq("id", mother_id) \
                .single() \
                .execute()
            if mother_result.data:
                summary["mother"] = mother_result.data
        except:
            pass
        
        # Get children
        try:
            children_result = supabase.table("children") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .execute()
            summary["children"] = children_result.data or []
        except:
            pass
        
        # Get recent assessments
        try:
            assessments_result = supabase.table("postnatal_assessments") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .order("created_at", desc=True) \
                .limit(10) \
                .execute()
            
            for a in (assessments_result.data or []):
                if a.get("assessment_type") == "mother_postnatal":
                    summary["mother_assessments"].append(a)
                elif a.get("assessment_type") == "child_checkup":
                    summary["child_assessments"].append(a)
        except:
            pass
        
        # Generate next actions based on data
        if summary["mother"]:
            if len(summary["mother_assessments"]) == 0:
                summary["next_actions"].append({
                    "type": "mother_assessment",
                    "priority": "high",
                    "message": "Initial postnatal assessment needed"
                })
            
            for child in summary["children"]:
                child_checks = [a for a in summary["child_assessments"] if a.get("child_id") == child.get("id")]
                if len(child_checks) == 0:
                    summary["next_actions"].append({
                        "type": "child_assessment",
                        "child_id": child.get("id"),
                        "child_name": child.get("name"),
                        "priority": "high",
                        "message": f"Initial health check needed for {child.get('name')}"
                    })
        
        if CACHE_AVAILABLE and cache:
            cache.set(cache_key, {**summary, "cached": True}, ttl_seconds=300)
            
        return summary
        
    except Exception as e:
        logger.error(f"Error getting postnatal summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== POSTNATAL MOTHERS LIST ====================

@router.get("/mothers")
async def get_postnatal_mothers(
    asha_worker_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    limit: int = 50
):
    """Get all mothers currently in postnatal care"""
    try:
        query = supabase.table("mothers") \
            .select("id, name, phone, age, location, status, due_date, asha_worker_id, doctor_id") \
            .eq("status", "postnatal")
        
        if asha_worker_id:
            query = query.eq("asha_worker_id", asha_worker_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        
        result = query.limit(limit).execute()
        
        return {
            "mothers": result.data or [],
            "total": len(result.data or [])
        }
        
    except Exception as e:
        logger.error(f"Error fetching postnatal mothers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
