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
    4. Returns success response
    
    After this, the mother will:
    - Stop appearing in MatruRaksha frontend
    - Start appearing in SantanRaksha frontend
    - All chatbot queries route to SantanRaksha agents (Postnatal, Pediatric, Vaccine, Growth)
    """
    try:
        logger.info(f"📋 Processing delivery completion for mother: {request.mother_id}")
        
        mother_updated = False
        child_created = None
        delivery_info_saved = False
        
        # Step 1: Update mother's status to 'postnatal' (using existing 'status' column)
        # The 'status' column exists in the mothers table
        try:
            # Try updating with status field that exists
            mother_result = supabase.table('mothers').update({
                'status': 'postnatal'  # Mark as postnatal - this signals she's in SantanRaksha mode
            }).eq('id', request.mother_id).execute()
            
            if mother_result.data:
                mother_updated = True
                logger.info(f"✅ Mother {request.mother_id} status updated to 'postnatal'")
        except Exception as e:
            logger.error(f"❌ Failed to update mother status: {e}")
        
        # Step 2: Store delivery details in a delivery_records table or notes
        # Since delivery-specific columns may not exist, store in a separate approach
        try:
            # Try to create a delivery record (if table exists)
            delivery_record = {
                'mother_id': request.mother_id,
                'delivery_date': request.delivery_date.isoformat(),
                'delivery_type': request.delivery_type,
                'delivery_hospital': request.delivery_hospital,
                'gestational_age_weeks': request.gestational_age_weeks,
                'delivery_complications': request.delivery_complications
            }
            # Try inserting into delivery_records table
            try:
                supabase.table('delivery_records').insert(delivery_record).execute()
                delivery_info_saved = True
                logger.info(f"📝 Delivery record saved")
            except:
                # Table might not exist - that's okay, we'll rely on status
                pass
        except Exception as e:
            logger.warning(f"⚠️ Could not save delivery record: {e}")
        
        # Step 2: Create child record if provided
        if request.child and request.child.name:
            try:
                # Check if children table exists
                child_data = {
                    'mother_id': request.mother_id,
                    'name': request.child.name,
                    'gender': request.child.gender or 'male',
                    'birth_date': request.delivery_date.date().isoformat()
                }
                
                if request.child.birth_weight_kg:
                    child_data['birth_weight_kg'] = float(request.child.birth_weight_kg)
                if request.child.birth_length_cm:
                    child_data['birth_length_cm'] = float(request.child.birth_length_cm)
                if request.child.birth_head_circumference_cm:
                    child_data['birth_head_circumference_cm'] = float(request.child.birth_head_circumference_cm)
                if request.child.apgar_score_1min is not None:
                    child_data['apgar_score_1min'] = request.child.apgar_score_1min
                if request.child.apgar_score_5min is not None:
                    child_data['apgar_score_5min'] = request.child.apgar_score_5min
                if request.child.birth_complications:
                    child_data['birth_complications'] = request.child.birth_complications
                
                child_result = supabase.table('children').insert(child_data).execute()
                
                if child_result.data and len(child_result.data) > 0:
                    child_created = child_result.data[0].get('id')
                    logger.info(f"👶 Child created: {child_created}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not create child record (table may not exist): {e}")
                # Child creation is optional - don't fail the delivery completion
        
        # Calculate days postpartum (handle timezone-aware vs naive comparison)
        try:
            delivery_dt = request.delivery_date
            # If delivery_date is timezone-aware, make it naive for comparison
            if delivery_dt.tzinfo is not None:
                delivery_dt = delivery_dt.replace(tzinfo=None)
            days_postpartum = max(0, (datetime.now() - delivery_dt).days)
        except Exception:
            days_postpartum = 0
        
        if mother_updated:
            logger.info(f"✅ Delivery completed successfully. Mother switched to SantanRaksha")
            
            return DeliveryCompletionResponse(
                success=True,
                message="Delivery completed successfully! Mother has been transitioned to SantanRaksha for postnatal care.",
                mother_updated=True,
                child_created=child_created,
                vaccination_schedule_created=False,  # Will implement when vaccination table exists
                active_system='santanraksha',
                days_postpartum=days_postpartum
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update mother record")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delivery completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Delivery completion failed: {str(e)}")


@router.get("/status/{mother_id}")
async def get_delivery_status(mother_id: str):
    """Get delivery status for a mother"""
    try:
        # Use existing 'status' column to determine if postnatal
        result = supabase.table('mothers').select(
            'id, name, status, due_date'
        ).eq('id', mother_id).single().execute()
        
        if result.data:
            data = result.data
            status = data.get('status', 'pregnant')
            is_postnatal = status == 'postnatal'
            
            return {
                "mother_id": mother_id,
                "name": data.get('name'),
                "delivery_status": 'delivered' if is_postnatal else 'pregnant',
                "active_system": 'santanraksha' if is_postnatal else 'matruraksha',
                "due_date": data.get('due_date'),
                "is_postnatal": is_postnatal
            }
        else:
            raise HTTPException(status_code=404, detail="Mother not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching delivery status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-child/{mother_id}")
async def add_child_post_delivery(mother_id: str, child: ChildData):
    """Add child information after delivery (if not added during delivery completion)"""
    try:
        # Get mother's status using existing 'status' column
        mother_result = supabase.table('mothers').select('status, due_date').eq('id', mother_id).single().execute()
        
        if not mother_result.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        status = mother_result.data.get('status', 'pregnant')
        if status != 'postnatal':
            raise HTTPException(status_code=400, detail="Delivery not completed yet. Complete delivery first.")
        
        # Use today as birth date if due_date not available
        due_date = mother_result.data.get('due_date')
        if due_date:
            birth_date = datetime.fromisoformat(due_date.replace('Z', '+00:00')).date()
        else:
            birth_date = datetime.now().date()
        
        # Create child record
        child_data = {
            'mother_id': mother_id,
            'name': child.name,
            'gender': child.gender,
            'birth_date': birth_date.isoformat()
        }
        
        # Add optional fields only if provided
        if child.birth_weight_kg:
            child_data['birth_weight_kg'] = float(child.birth_weight_kg)
        if child.birth_length_cm:
            child_data['birth_length_cm'] = float(child.birth_length_cm)
        if child.birth_head_circumference_cm:
            child_data['birth_head_circumference_cm'] = float(child.birth_head_circumference_cm)
        if child.apgar_score_1min is not None:
            child_data['apgar_score_1min'] = child.apgar_score_1min
        if child.apgar_score_5min is not None:
            child_data['apgar_score_5min'] = child.apgar_score_5min
        if child.birth_complications:
            child_data['birth_complications'] = child.birth_complications
        
        try:
            child_result = supabase.table('children').insert(child_data).execute()
            
            if child_result.data:
                child_id = child_result.data[0].get('id')
                logger.info(f"👶 Child added post-delivery: {child_id}")
                
                return {
                    "success": True,
                    "message": "Child added successfully",
                    "child_id": child_id,
                    "vaccination_schedule_created": False  # Will implement when vaccination table exists
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create child record")
        except Exception as table_err:
            logger.warning(f"⚠️ Children table may not exist: {table_err}")
            raise HTTPException(status_code=500, detail="Children table not available. Please run database migration.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding child: {e}")
        raise HTTPException(status_code=500, detail=str(e))
