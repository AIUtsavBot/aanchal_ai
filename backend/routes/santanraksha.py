"""
SantanRaksha - Child Health Tracking Routes
File: backend/routes/santanraksha.py

Endpoints for:
- Vaccination management (mark done, schedule)
- Growth monitoring (records, z-score calculation)
- Milestone tracking (toggle achievement, progress)
- Send telegram notifications for assessments
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging
import json
import math

# Import Supabase client
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

# Import growth agent for z-score calculations
try:
    from agents.growth_agent import GrowthAgent
    growth_agent = GrowthAgent()
except:
    growth_agent = None

# Import telegram service for notifications
try:
    from services.telegram_service import send_assessment_notification
except:
    send_assessment_notification = None

# Import access control utilities
try:
    from utils.access_control import (
        get_authorized_children,
        verify_child_access,
        verify_mother_access
    )
except ImportError as e:
    logger.warning(f"Access control not available: {e}")
    # Fallback functions
    async def get_authorized_children(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Access control not configured")
    async def verify_child_access(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Access control not configured")
    async def verify_mother_access(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Access control not configured")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/santanraksha", tags=["SantanRaksha"])


# ==================== AUTHENTICATION HELPER ====================

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract user info from Authorization header
    Expected format: Bearer {token} or user_id:{user_id},role:{role}
    """
    if not authorization:
        # For backwards compatibility, return admin access if no auth
        logger.warning("No authorization header, defaulting to ADMIN access")
        return {"user_id": "system", "role": "ADMIN"}
    
    try:
        # Try to parse custom format: user_id:xxx,role:yyy
        if "user_id:" in authorization and "role:" in authorization:
            parts = authorization.split(",")
            user_id = parts[0].split(":")[1].strip()
            role = parts[1].split(":")[1].strip()
            return {"user_id": user_id, "role": role}
        
        # Otherwise assume it's a token and decode
        # For now, return admin access
        logger.warning("Token-based auth not implemented, defaulting to ADMIN")
        return {"user_id": "system", "role": "ADMIN"}
    except Exception as e:
        logger.error(f"Error parsing authorization: {e}")
        return {"user_id": "system", "role": "ADMIN"}


# ==================== PYDANTIC MODELS ====================

class VaccinationMarkDone(BaseModel):
    child_id: str
    vaccine_name: str
    given_date: Optional[str] = None  # Defaults to today
    given_by: Optional[str] = None
    notes: Optional[str] = None
    batch_number: Optional[str] = None
    administered_at: Optional[str] = None  # Hospital/clinic name


class GrowthRecordCreate(BaseModel):
    child_id: str
    weight_kg: float
    height_cm: Optional[float] = None
    head_circumference_cm: Optional[float] = None
    notes: Optional[str] = None
    measured_by: Optional[str] = None
    measurement_date: Optional[str] = None  # Defaults to today


class MilestoneToggle(BaseModel):
    child_id: str
    milestone_name: str
    milestone_category: str
    notes: Optional[str] = None


class AssessmentNotification(BaseModel):
    mother_id: str
    child_id: Optional[str] = None
    assessment_type: str  # 'growth', 'vaccine', 'milestone', 'health_check'
    summary: str
    recommendations: List[str] = []
    risk_level: Optional[str] = "normal"
    language: Optional[str] = "hindi"


# ==================== WHO GROWTH STANDARDS ====================

# Median weights for boys (kg) by age in months
WHO_WEIGHT_MALE = {
    0: 3.3, 1: 4.5, 2: 5.6, 3: 6.4, 4: 7.0, 5: 7.5,
    6: 7.9, 9: 9.2, 12: 10.2, 18: 11.8, 24: 12.9
}

WHO_WEIGHT_FEMALE = {
    0: 3.2, 1: 4.2, 2: 5.1, 3: 5.8, 4: 6.4, 5: 6.9,
    6: 7.3, 9: 8.6, 12: 9.5, 18: 11.0, 24: 12.1
}

WHO_HEIGHT_MALE = {
    0: 49.9, 1: 54.7, 2: 58.4, 3: 61.4, 4: 63.9, 5: 65.9,
    6: 67.6, 9: 72.0, 12: 75.7, 18: 82.3, 24: 87.8
}

WHO_HEIGHT_FEMALE = {
    0: 49.1, 1: 53.7, 2: 57.1, 3: 59.8, 4: 62.1, 5: 64.0,
    6: 65.7, 9: 70.1, 12: 74.0, 18: 80.7, 24: 86.4
}


def get_child_age_months(birth_date_str: str) -> int:
    """Calculate child's age in months from birth date string"""
    try:
        birth_date = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
        now = datetime.now()
        months = (now.year - birth_date.year) * 12 + (now.month - birth_date.month)
        return max(0, months)
    except:
        return 0


def calculate_z_scores(weight_kg: float, height_cm: Optional[float], 
                       age_months: int, gender: str) -> Dict[str, float]:
    """Calculate WHO z-scores for weight and height"""
    z_scores = {}
    
    # Select reference table based on gender
    weight_table = WHO_WEIGHT_MALE if gender.lower() == 'male' else WHO_WEIGHT_FEMALE
    height_table = WHO_HEIGHT_MALE if gender.lower() == 'male' else WHO_HEIGHT_FEMALE
    
    # Find closest age in tables
    closest_age = min(weight_table.keys(), key=lambda x: abs(x - age_months))
    
    # Weight-for-age z-score
    median_weight = weight_table.get(closest_age, 10.0)
    sd_weight = median_weight * 0.15  # Approximate SD
    if median_weight > 0:
        wfa_z = (weight_kg - median_weight) / sd_weight
        z_scores['weight_for_age_z'] = round(wfa_z, 2)
    
    # Height-for-age z-score
    if height_cm and height_cm > 0:
        closest_age_h = min(height_table.keys(), key=lambda x: abs(x - age_months))
        median_height = height_table.get(closest_age_h, 75.0)
        sd_height = median_height * 0.05
        if median_height > 0:
            hfa_z = (height_cm - median_height) / sd_height
            z_scores['height_for_age_z'] = round(hfa_z, 2)
    
    return z_scores


def get_growth_status(wfa_z: float) -> Dict[str, Any]:
    """Interpret z-score and return status with recommendations"""
    if wfa_z < -3:
        return {
            'status': 'severe_acute_malnutrition',
            'label': 'Severely Underweight',
            'alert': True,
            'color': '#ef4444',
            'recommendations': [
                '🚨 URGENT: Refer to hospital immediately',
                'Start therapeutic feeding (RUTF)',
                'Monitor weight every 3 days'
            ]
        }
    elif wfa_z < -2:
        return {
            'status': 'moderate_acute_malnutrition',
            'label': 'Underweight',
            'alert': True,
            'color': '#f59e0b',
            'recommendations': [
                '⚠️ Enhanced feeding needed',
                'Add energy-dense foods (ghee, oil)',
                'Increase meal frequency to 6x/day',
                'Monitor weight every week'
            ]
        }
    elif wfa_z > 2:
        return {
            'status': 'overweight',
            'label': 'Overweight',
            'alert': True,
            'color': '#f59e0b',
            'recommendations': [
                'Reduce fried/sugary foods',
                'Increase physical activity',
                'Monitor portion sizes'
            ]
        }
    else:
        return {
            'status': 'normal',
            'label': 'Normal Growth',
            'alert': False,
            'color': '#10b981',
            'recommendations': [
                '✅ Great! Continue current feeding',
                'Maintain dietary diversity (4+ food groups)'
            ]
        }


# ==================== VACCINATION ENDPOINTS ====================

@router.post("/vaccination/mark-done")
async def mark_vaccination_done(
    data: VaccinationMarkDone,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a vaccination as completed
    Updates the vaccinations table with status='completed'
    Uses actual DB columns: administered_date, administered_by, administered_at_facility
    """
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=data.child_id
        )
        
        logger.info(f"💉 Marking vaccine as done: {data.vaccine_name} for child {data.child_id}")
        
        administered_date = data.given_date or datetime.now().date().isoformat()
        
        # First, check if there's an existing pending/scheduled vaccination record
        existing = supabase.table("vaccinations") \
            .select("id") \
            .eq("child_id", data.child_id) \
            .eq("vaccine_name", data.vaccine_name) \
            .neq("status", "completed") \
            .execute()
        
        if existing.data:
            # Update existing record
            record_id = existing.data[0].get('id')
            result = supabase.table("vaccinations").update({
                "status": "completed",
                "administered_date": administered_date,
                "administered_by": data.given_by,
                "notes": data.notes,
                "batch_number": data.batch_number,
                "administered_at_facility": data.administered_at,
                "updated_at": datetime.now().isoformat()
            }).eq("id", record_id).execute()
            
            logger.info(f"✅ Updated existing vaccination record: {record_id}")
        else:
            # Create new completed record
            result = supabase.table("vaccinations").insert({
                "child_id": data.child_id,
                "vaccine_name": data.vaccine_name,
                "vaccine_category": "primary",
                "recommended_age_days": 0,
                "status": "completed",
                "administered_date": administered_date,
                "due_date": administered_date,
                "administered_by": data.given_by,
                "notes": data.notes,
                "batch_number": data.batch_number,
                "administered_at_facility": data.administered_at,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            logger.info(f"✅ Created new vaccination record")
        
        return {
            "success": True,
            "message": f"Vaccine '{data.vaccine_name}' marked as completed",
            "vaccine_name": data.vaccine_name,
            "administered_date": administered_date
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking vaccination done: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vaccination/{child_id}")
async def get_child_vaccinations(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all vaccination records for a child"""
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=child_id
        )
        result = supabase.table("vaccinations") \
            .select("*") \
            .eq("child_id", child_id) \
            .order("due_date", desc=False) \
            .execute()
        
        return {
            "child_id": child_id,
            "vaccinations": result.data or [],
            "completed_count": len([v for v in (result.data or []) if v.get('status') == 'completed']),
            "pending_count": len([v for v in (result.data or []) if v.get('status') != 'completed'])
        }
        
    except Exception as e:
        logger.error(f"Error fetching vaccinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vaccination/{child_id}/initialize")
async def initialize_vaccination_schedule(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize the IAP 2023 vaccination schedule for a child
    Creates pending vaccination records based on birth date
    """
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=child_id
        )
        
        # Get child info
        child_result = supabase.table("children") \
            .select("id, name, birth_date") \
            .eq("id", child_id) \
            .limit(1) \
            .execute()
        
        if not child_result.data or len(child_result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Child not found with ID: {child_id}")
        
        child = child_result.data[0]
        birth_date = datetime.fromisoformat(child['birth_date'].replace('Z', '+00:00')).date()
        
        # IAP 2023 Schedule with categories
        IAP_SCHEDULE = [
            {'name': 'BCG', 'age_days': 0, 'category': 'birth'},
            {'name': 'OPV-0', 'age_days': 0, 'category': 'birth'},
            {'name': 'Hepatitis B-1', 'age_days': 0, 'category': 'birth'},
            {'name': 'OPV-1 + IPV-1', 'age_days': 42, 'category': 'primary'},
            {'name': 'Pentavalent-1', 'age_days': 42, 'category': 'primary'},
            {'name': 'Rotavirus-1', 'age_days': 42, 'category': 'primary'},
            {'name': 'PCV-1', 'age_days': 42, 'category': 'primary'},
            {'name': 'OPV-2 + IPV-2', 'age_days': 70, 'category': 'primary'},
            {'name': 'Pentavalent-2', 'age_days': 70, 'category': 'primary'},
            {'name': 'Rotavirus-2', 'age_days': 70, 'category': 'primary'},
            {'name': 'OPV-3 + IPV-3', 'age_days': 98, 'category': 'primary'},
            {'name': 'Pentavalent-3', 'age_days': 98, 'category': 'primary'},
            {'name': 'Rotavirus-3', 'age_days': 98, 'category': 'primary'},
            {'name': 'PCV-2', 'age_days': 98, 'category': 'primary'},
            {'name': 'Measles-1 (MR/MMR)', 'age_days': 270, 'category': 'primary'},
            {'name': 'Vitamin A-1', 'age_days': 270, 'category': 'primary'},
            {'name': 'PCV Booster', 'age_days': 365, 'category': 'booster'},
            {'name': 'Measles-2 (MMR)', 'age_days': 450, 'category': 'booster'},
            {'name': 'DPT Booster-1', 'age_days': 540, 'category': 'booster'},
        ]
        
        # Check existing vaccinations
        existing = supabase.table("vaccinations") \
            .select("vaccine_name") \
            .eq("child_id", child_id) \
            .execute()
        existing_names = [v['vaccine_name'] for v in (existing.data or [])]
        
        # Create schedule entries for missing vaccines
        new_records = []
        today = date.today()
        
        for vax in IAP_SCHEDULE:
            if vax['name'] not in existing_names:
                from datetime import timedelta
                due_date = birth_date + timedelta(days=vax['age_days'])
                
                # Determine status
                if due_date < today:
                    status = 'overdue'
                elif (due_date - today).days <= 7:
                    status = 'pending'  # Due soon
                else:
                    status = 'pending'
                
                new_records.append({
                    'child_id': child_id,
                    'vaccine_name': vax['name'],
                    'vaccine_category': vax['category'],
                    'recommended_age_days': vax['age_days'],
                    'due_date': due_date.isoformat(),
                    'status': status,
                    'created_at': datetime.now().isoformat()
                })
        
        if new_records:
            supabase.table("vaccinations").insert(new_records).execute()
        
        return {
            "success": True,
            "message": f"Initialized {len(new_records)} vaccination records for {child['name']}",
            "child_id": child_id,
            "vaccines_created": len(new_records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing vaccination schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GROWTH MONITORING ENDPOINTS ====================

@router.post("/growth/record")
async def add_growth_record(
    data: GrowthRecordCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a growth record and calculate z-scores automatically
    Returns growth assessment with recommendations
    Uses actual DB columns: weight_for_age_z_score, height_for_age_z_score, age_months, age_days
    """
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=data.child_id
        )
        
        logger.info(f"📏 Adding growth record for child: {data.child_id}")
        
        # Get child info for age and gender (don't use .single() as it throws on empty result)
        child_result = supabase.table("children") \
            .select("id, name, birth_date, gender") \
            .eq("id", data.child_id) \
            .limit(1) \
            .execute()
        
        if not child_result.data or len(child_result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Child not found with ID: {data.child_id}")
        
        child = child_result.data[0]
        
        # Calculate age in months and days
        birth_date_str = child.get('birth_date', '')
        try:
            birth_date = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
            now = datetime.now()
            total_days = (now - birth_date).days
            age_months = total_days // 30
            age_days = total_days
        except:
            age_months = 0
            age_days = 0
        
        gender = child.get('gender', 'male')
        
        # Calculate z-scores
        z_scores = calculate_z_scores(
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            age_months=age_months,
            gender=gender
        )
        
        # Get growth status
        wfa_z = z_scores.get('weight_for_age_z', 0)
        growth_status = get_growth_status(wfa_z)
        
        # Prepare record with correct column names matching actual DB schema
        measurement_date = data.measurement_date or datetime.now().date().isoformat()
        
        record_data = {
            "child_id": data.child_id,
            "measurement_date": measurement_date,
            "age_months": age_months,
            "age_days": age_days,
            "weight_kg": data.weight_kg,
            "height_cm": data.height_cm,
            "head_circumference_cm": data.head_circumference_cm,
            "weight_for_age_z_score": z_scores.get('weight_for_age_z'),
            "height_for_age_z_score": z_scores.get('height_for_age_z'),
            "growth_status": growth_status['status'],
            "notes": data.notes,
            "alert_generated": growth_status['alert'],
            "created_at": datetime.now().isoformat()
        }
        
        # Add measured_by as UUID if it's a valid user_profile id, otherwise store in notes
        if data.measured_by:
            # Store measured_by info in notes since it expects UUID
            if record_data.get('notes'):
                record_data['notes'] = f"{record_data['notes']} | Measured by: {data.measured_by}"
            else:
                record_data['notes'] = f"Measured by: {data.measured_by}"
        
        # Insert record
        result = supabase.table("growth_records").insert(record_data).execute()
        
        if result.data:
            logger.info(f"✅ Growth record saved with z-scores: WFA={wfa_z}")
            
            return {
                "success": True,
                "message": "Growth record saved successfully",
                "record_id": result.data[0].get('id'),
                "z_scores": {
                    "weight_for_age_z": z_scores.get('weight_for_age_z'),
                    "height_for_age_z": z_scores.get('height_for_age_z')
                },
                "growth_status": growth_status['status'],
                "status_label": growth_status['label'],
                "alert": growth_status['alert'],
                "recommendations": growth_status['recommendations'],
                "age_months": age_months
            }
        
        raise HTTPException(status_code=500, detail="Failed to save growth record")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding growth record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/growth/{child_id}")
async def get_child_growth_records(
    child_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get growth history for a child with trend analysis"""
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=child_id
        )
        result = supabase.table("growth_records") \
            .select("*") \
            .eq("child_id", child_id) \
            .order("measurement_date", desc=True) \
            .limit(limit) \
            .execute()
        
        records = result.data or []
        
        # Calculate trend if we have multiple records
        trend = None
        if len(records) >= 2:
            latest = records[0]
            previous = records[1]
            weight_change = (latest.get('weight_kg', 0) or 0) - (previous.get('weight_kg', 0) or 0)
            trend = {
                'direction': 'gaining' if weight_change > 0 else 'losing' if weight_change < 0 else 'stable',
                'weight_change_kg': round(weight_change, 2),
                'message': f"{'Gained' if weight_change > 0 else 'Lost'} {abs(round(weight_change, 2))} kg since last measurement"
            }
        
        return {
            "child_id": child_id,
            "records": records,
            "total": len(records),
            "trend": trend,
            "latest": records[0] if records else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching growth records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MILESTONE TRACKING ENDPOINTS ====================

@router.post("/milestone/toggle")
async def toggle_milestone(
    data: MilestoneToggle,
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle a developmental milestone as achieved/not achieved
    Uses actual DB columns: category (not milestone_category), is_achieved, achieved_age_months, etc.
    """
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=data.child_id
        )
        
        logger.info(f"🎯 Toggling milestone '{data.milestone_name}' for child {data.child_id}")
        
        # Check if milestone already exists for this child
        existing = supabase.table("milestones") \
            .select("id, is_achieved") \
            .eq("child_id", data.child_id) \
            .eq("milestone_name", data.milestone_name) \
            .execute()
        
        if existing.data:
            record_id = existing.data[0]['id']
            is_currently_achieved = existing.data[0].get('is_achieved', False)
            
            if is_currently_achieved:
                # Mark as not achieved (toggle off)
                supabase.table("milestones").update({
                    "is_achieved": False,
                    "achieved_date": None,
                    "achieved_age_months": None,
                    "achieved_age_days": None,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", record_id).execute()
                
                return {
                    "success": True,
                    "action": "unmarked",
                    "message": f"Milestone '{data.milestone_name}' unmarked",
                    "achieved": False
                }
            else:
                # Get child's age for achieved_age calculation
                child_result = supabase.table("children") \
                    .select("birth_date") \
                    .eq("id", data.child_id) \
                    .limit(1) \
                    .execute()
                
                achieved_age_months = 0
                achieved_age_days = 0
                if child_result.data and len(child_result.data) > 0:
                    try:
                        birth_date = datetime.fromisoformat(child_result.data[0]['birth_date'].replace('Z', '+00:00'))
                        now = datetime.now()
                        achieved_age_days = (now - birth_date).days
                        achieved_age_months = achieved_age_days // 30
                    except:
                        pass
                
                # Mark as achieved (toggle on)
                supabase.table("milestones").update({
                    "is_achieved": True,
                    "achieved_date": datetime.now().date().isoformat(),
                    "achieved_age_months": achieved_age_months,
                    "achieved_age_days": achieved_age_days,
                    "notes": data.notes,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", record_id).execute()
                
                return {
                    "success": True,
                    "action": "achieved",
                    "message": f"Milestone '{data.milestone_name}' achieved! 🎉",
                    "achieved": True,
                    "record_id": record_id
                }
        else:
            # Create new milestone record as achieved
            # Get child's age for achieved_age calculation
            child_result = supabase.table("children") \
                .select("birth_date") \
                .eq("id", data.child_id) \
                .limit(1) \
                .execute()
            
            achieved_age_months = 0
            achieved_age_days = 0
            if child_result.data and len(child_result.data) > 0:
                try:
                    birth_date = datetime.fromisoformat(child_result.data[0]['birth_date'].replace('Z', '+00:00'))
                    now = datetime.now()
                    achieved_age_days = (now - birth_date).days
                    achieved_age_months = achieved_age_days // 30
                except:
                    pass
            
            # Map milestone category to DB enum values
            category_map = {
                'Motor': 'gross_motor',
                'Fine Motor': 'fine_motor',
                'Language': 'language',
                'Cognitive': 'cognitive',
                'Social': 'social_emotional',
                'Sensory': 'cognitive',  # Map sensory to cognitive
                'Self Care': 'self_care'
            }
            category = category_map.get(data.milestone_category, 'gross_motor')
            
            result = supabase.table("milestones").insert({
                "child_id": data.child_id,
                "milestone_name": data.milestone_name,
                "category": category,  # Using correct column name
                "expected_age_months": achieved_age_months,  # Required field
                "is_achieved": True,
                "achieved_date": datetime.now().date().isoformat(),
                "achieved_age_months": achieved_age_months,
                "achieved_age_days": achieved_age_days,
                "notes": data.notes,
                "observation_method": "parent_report",
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return {
                "success": True,
                "action": "added",
                "message": f"Milestone '{data.milestone_name}' achieved! 🎉",
                "achieved": True,
                "record_id": result.data[0].get('id') if result.data else None
            }
        
    except Exception as e:
        logger.error(f"❌ Error toggling milestone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestone/{child_id}")
async def get_child_milestones(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all achieved milestones for a child"""
    try:
        # Verify user has access to this child
        await verify_child_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            child_id=child_id
        )
        result = supabase.table("milestones") \
            .select("*") \
            .eq("child_id", child_id) \
            .eq("is_achieved", True) \
            .order("achieved_date", desc=True) \
            .execute()
        
        # Group by category
        by_category = {}
        for m in (result.data or []):
            category = m.get('category', 'Other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(m)
        
        return {
            "child_id": child_id,
            "milestones": result.data or [],
            "by_category": by_category,
            "total_achieved": len(result.data or [])
        }
        
    except Exception as e:
        logger.error(f"Error fetching milestones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NOTIFICATION ENDPOINTS ====================

@router.post("/notify/assessment")
async def send_assessment_notification_telegram(
    data: AssessmentNotification,
    current_user: dict = Depends(get_current_user)
):
    """
    Send assessment result to mother via Telegram
    Used after growth, vaccine, or milestone assessments
    """
    try:
        # Verify user has access to this mother
        await verify_mother_access(
            supabase_client=supabase,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            mother_id=data.mother_id
        )
        
        logger.info(f"📱 Sending {data.assessment_type} notification for mother: {data.mother_id}")
        
        # Get mother's telegram chat ID
        mother_result = supabase.table("mothers") \
            .select("name, phone, telegram_chat_id, preferred_language") \
            .eq("id", data.mother_id) \
            .limit(1) \
            .execute()
        
        if not mother_result.data or len(mother_result.data) == 0:
            return {
                "success": False,
                "message": "Mother not found"
            }
        
        mother = mother_result.data[0]
        chat_id = mother.get('telegram_chat_id')
        
        if not chat_id:
            return {
                "success": False,
                "message": "Mother doesn't have Telegram connected"
            }
        
        # Format message
        language = data.language or mother.get('preferred_language', 'hindi')
        
        if language == 'hindi':
            emoji_map = {
                'growth': '📏',
                'vaccine': '💉',
                'milestone': '🎯',
                'health_check': '🏥'
            }
            type_names = {
                'growth': 'वृद्धि जांच',
                'vaccine': 'टीकाकरण',
                'milestone': 'विकास मील का पत्थर',
                'health_check': 'स्वास्थ्य जांच'
            }
            
            message = f"""
{emoji_map.get(data.assessment_type, '📋')} *{type_names.get(data.assessment_type, 'जांच')} रिपोर्ट*

नमस्ते {mother['name']} जी! 🙏

{data.summary}

"""
            if data.recommendations:
                message += "*सुझाव:*\n"
                for rec in data.recommendations:
                    message += f"• {rec}\n"
            
            if data.risk_level == 'high':
                message += "\n⚠️ *महत्वपूर्ण:* कृपया जल्द से जल्द डॉक्टर से मिलें!"
        else:
            emoji_map = {
                'growth': '📏',
                'vaccine': '💉',
                'milestone': '🎯',
                'health_check': '🏥'
            }
            
            message = f"""
{emoji_map.get(data.assessment_type, '📋')} *{data.assessment_type.replace('_', ' ').title()} Report*

Hello {mother['name']}! 🙏

{data.summary}

"""
            if data.recommendations:
                message += "*Recommendations:*\n"
                for rec in data.recommendations:
                    message += f"• {rec}\n"
            
            if data.risk_level == 'high':
                message += "\n⚠️ *Important:* Please visit a doctor soon!"
        
        # Send via telegram
        if send_assessment_notification:
            await send_assessment_notification(chat_id, message)
            logger.info(f"✅ Telegram notification sent to {mother['name']}")
            return {
                "success": True,
                "message": "Notification sent via Telegram"
            }
        else:
            logger.warning("⚠️ Telegram service not available")
            return {
                "success": False,
                "message": "Telegram service not configured"
            }
        
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")
        return {
            "success": False,
            "message": str(e)
        }


# ==================== DASHBOARD SUMMARY ENDPOINT ====================

@router.get("/child/{child_id}/dashboard")
async def get_child_dashboard(child_id: str):
    """
    Get complete dashboard data for a child
    Includes latest growth, vaccination status, and milestones
    """
    try:
        # Get child info
        child_result = supabase.table("children") \
            .select("*, mothers:mother_id(name, phone, telegram_chat_id)") \
            .eq("id", child_id) \
            .limit(1) \
            .execute()
        
        if not child_result.data or len(child_result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Child not found with ID: {child_id}")
        
        child = child_result.data[0]
        age_months = get_child_age_months(child.get('birth_date', ''))
        
        # Get latest growth
        growth_result = supabase.table("growth_records") \
            .select("*") \
            .eq("child_id", child_id) \
            .order("measurement_date", desc=True) \
            .limit(1) \
            .execute()
        
        # Get vaccination stats
        vax_result = supabase.table("vaccinations") \
            .select("status") \
            .eq("child_id", child_id) \
            .execute()
        
        completed_vaccines = len([v for v in (vax_result.data or []) if v['status'] == 'completed'])
        pending_vaccines = len([v for v in (vax_result.data or []) if v['status'] != 'completed'])
        overdue_vaccines = len([v for v in (vax_result.data or []) if v['status'] == 'overdue'])
        
        # Get milestone count
        milestone_result = supabase.table("milestones") \
            .select("id") \
            .eq("child_id", child_id) \
            .execute()
        
        return {
            "child": {
                "id": child.get('id'),
                "name": child.get('name'),
                "gender": child.get('gender'),
                "birth_date": child.get('birth_date'),
                "age_months": age_months
            },
            "mother": child.get('mothers'),
            "growth": {
                "latest_record": growth_result.data[0] if growth_result.data else None,
                "has_records": len(growth_result.data or []) > 0
            },
            "vaccinations": {
                "completed": completed_vaccines,
                "pending": pending_vaccines,
                "overdue": overdue_vaccines,
                "total": completed_vaccines + pending_vaccines
            },
            "milestones": {
                "achieved": len(milestone_result.data or [])
            },
            "alerts": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching child dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
