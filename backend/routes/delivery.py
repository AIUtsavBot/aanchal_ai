"""
Delivery Completion API Endpoint
Handles the transition from MatruRaksha (pregnancy) to SantanRaksha (postnatal+child)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import logging

# Supabase client
try:
    from services.supabase_service import supabase
except ImportError:
    try:
        from backend.services.supabase_service import supabase
    except ImportError:
        supabase = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/delivery", tags=["Delivery"])


class ChildData(BaseModel):
    """Child information for delivery completion"""
    name: str = Field(..., description="Child's name")
    gender: str = Field("male", description="Child's gender: male/female/other")
    birth_weight_kg: Optional[Decimal] = Field(None, description="Birth weight in kg")
    birth_length_cm: Optional[Decimal] = Field(None, description="Birth length in cm")
    birth_head_circumference_cm: Optional[Decimal] = Field(None, description="Head circumference in cm")
    apgar_score_1min: Optional[int] = Field(None, ge=0, le=10, description="APGAR score at 1 minute")
    apgar_score_5min: Optional[int] = Field(None, ge=0, le=10, description="APGAR score at 5 minutes")
    birth_complications: List[str] = Field(default_factory=list, description="Birth complications")


class DeliveryCompletionRequest(BaseModel):
    """Request to mark delivery as completed"""
    mother_id: str = Field(..., description="Mother's UUID")
    delivery_date: datetime = Field(..., description="Date and time of delivery")
    delivery_type: str = Field(..., description="Type of delivery: normal/cesarean/assisted/forceps/vacuum")
    delivery_hospital: Optional[str] = Field(None, description="Hospital/facility name")
    delivery_complications: List[str] = Field(default_factory=list, description="Delivery complications")
    gestational_age_weeks: Optional[int] = Field(None, ge=20, le=45, description="Gestational age at delivery in weeks")
    
    # Child information (optional - can be added later)
    child: Optional[ChildData] = Field(None, description="Newborn child information")


class DeliveryCompletionResponse(BaseModel):
    """Response after delivery completion"""
    success: bool
    message: str
    mother_updated: bool
    child_created: Optional[str] = None  # Child UUID if created
    vaccination_schedule_created: bool = False
    active_system: str  # 'santanraksha'
    days_postpartum: int = 0


@router.post("/complete", response_model=DeliveryCompletionResponse)
async def complete_delivery(request: DeliveryCompletionRequest):
    """
    Complete delivery and transition mother from MatruRaksha to SantanRaksha
    
    This endpoint:
    1. Updates mother's delivery status
    2. Switches active_system from 'matruraksha' to 'santanraksha'
    3. Creates child record (if provided)
    4. Auto-generates IAP 2023 vaccination schedule
    5. Triggers postnatal care timeline
    
    After this, the mother will:
    - Stop appearing in MatruRaksha frontend
    - Start appearing in SantanRaksha frontend
    - All chatbot queries route to SantanRaksha agents (Postnatal, Pediatric, Vaccine, Growth)
    """
    try:
        logger.info(f"📋 Processing delivery completion for mother: {request.mother_id}")
        
        # Call the database function
        result = supabase.rpc(
            'complete_delivery',
            {
                'p_mother_id': request.mother_id,
                'p_delivery_date': request.delivery_date.isoformat(),
                'p_delivery_type': request.delivery_type,
                'p_delivery_hospital': request.delivery_hospital,
                'p_delivery_complications': request.delivery_complications,
                'p_gestational_age_weeks': request.gestational_age_weeks,
                # Child data
                'p_child_name': request.child.name if request.child else None,
                'p_child_gender': request.child.gender if request.child else 'male',
                'p_birth_weight_kg': float(request.child.birth_weight_kg) if request.child and request.child.birth_weight_kg else None,
                'p_birth_length_cm': float(request.child.birth_length_cm) if request.child and request.child.birth_length_cm else None,
                'p_birth_head_circumference_cm': float(request.child.birth_head_circumference_cm) if request.child and request.child.birth_head_circumference_cm else None,
                'p_apgar_score_1min': request.child.apgar_score_1min if request.child else None,
                'p_apgar_score_5min': request.child.apgar_score_5min if request.child else None,
                'p_birth_complications': request.child.birth_complications if request.child else []
            }
        ).execute()
        
        if result.data and len(result.data) > 0:
            response_data = result.data[0]
            
            # Calculate days postpartum
            days_postpartum = (datetime.now() - request.delivery_date).days
            
            logger.info(f"✅ Delivery completed successfully. Mother switched to SantanRaksha")
            if response_data.get('child_created'):
                logger.info(f"👶 Child created: {response_data['child_created']}")
            if response_data.get('vaccination_schedule_created'):
                logger.info(f"💉 Vaccination schedule generated")
            
            return DeliveryCompletionResponse(
                success=True,
                message="Delivery completed successfully! Mother has been transitioned to SantanRaksha for postnatal care.",
                mother_updated=response_data.get('mother_updated', False),
                child_created=response_data.get('child_created'),
                vaccination_schedule_created=response_data.get('vaccination_schedule_created', False),
                active_system=response_data.get('system_switched', 'santanraksha'),
                days_postpartum=days_postpartum
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to complete delivery - no response from database")
            
    except Exception as e:
        logger.error(f"❌ Delivery completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Delivery completion failed: {str(e)}")


@router.get("/status/{mother_id}")
async def get_delivery_status(mother_id: str):
    """Get delivery status for a mother"""
    try:
        result = supabase.table('mothers').select(
            'delivery_status, delivery_date, delivery_type, active_system, delivery_hospital'
        ).eq('id', mother_id).single().execute()
        
        if result.data:
            data = result.data
            days_postpartum = None
            if data.get('delivery_date'):
                delivery_dt = datetime.fromisoformat(data['delivery_date'].replace('Z', '+00:00'))
                days_postpartum = (datetime.now() - delivery_dt).days
            
            return {
                "mother_id": mother_id,
                "delivery_status": data.get('delivery_status', 'pregnant'),
                "active_system": data.get('active_system', 'matruraksha'),
                "delivery_date": data.get('delivery_date'),
                "delivery_type": data.get('delivery_type'),
                "delivery_hospital": data.get('delivery_hospital'),
                "days_postpartum": days_postpartum,
                "is_postnatal": data.get('active_system') == 'santanraksha'
            }
        else:
            raise HTTPException(status_code=404, detail="Mother not found")
            
    except Exception as e:
        logger.error(f"Error fetching delivery status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-child/{mother_id}")
async def add_child_post_delivery(mother_id: str, child: ChildData):
    """Add child information after delivery (if not added during delivery completion)"""
    try:
        # Get mother's delivery date
        mother_result = supabase.table('mothers').select('delivery_date, active_system').eq('id', mother_id).single().execute()
        
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        if mother_result.data.get('active_system') != 'santanraksha':
            raise HTTPException(status_code=400, detail="Delivery not completed yet. Complete delivery first.")
        
        delivery_date = mother_result.data.get('delivery_date')
        if not delivery_date:
            raise HTTPException(status_code=400, detail="Delivery date not set")
        
        birth_date = datetime.fromisoformat(delivery_date.replace('Z', '+00:00')).date()
        
        # Create child record
        child_data = {
            'mother_id': mother_id,
            'name': child.name,
            'gender': child.gender,
            'birth_date': birth_date.isoformat(),
            'birth_weight_kg': float(child.birth_weight_kg) if child.birth_weight_kg else None,
            'birth_length_cm': float(child.birth_length_cm) if child.birth_length_cm else None,
            'birth_head_circumference_cm': float(child.birth_head_circumference_cm) if child.birth_head_circumference_cm else None,
            'apgar_score_1min': child.apgar_score_1min,
            'apgar_score_5min': child.apgar_score_5min,
            'birth_complications': child.birth_complications
        }
        
        child_result = supabase.table('children').insert(child_data).execute()
        
        if child_result.data:
            child_id = child_result.data[0]['id']
            
            # Generate vaccination schedule
            supabase.rpc('generate_vaccination_schedule', {
                'p_child_id': child_id,
                'p_birth_date': birth_date.isoformat()
            }).execute()
            
            logger.info(f"👶 Child added post-delivery: {child_id}")
            
            return {
                "success": True,
                "message": "Child added successfully",
                "child_id": child_id,
                "vaccination_schedule_created": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create child record")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding child: {e}")
        raise HTTPException(status_code=500, detail=str(e))
