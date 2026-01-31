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

# Import cache service
try:
    from services.cache_service import cached, invalidate_mothers_cache
except ImportError:
    try:
        from backend.services.cache_service import cached, invalidate_mothers_cache
    except ImportError:
        # Dummy implementations if cache missing
        def cached(*args, **kwargs): return lambda x: x
        def invalidate_mothers_cache(): pass

# Import congratulations service
try:
    from services.congratulations_service import generate_congratulations_message, get_default_congratulations
except ImportError:
    try:
        from backend.services.congratulations_service import generate_congratulations_message, get_default_congratulations
    except ImportError:
        # Fallback if service missing
        async def generate_congratulations_message(*args, **kwargs): 
            return "Congratulations on your delivery! Welcome to SantanRaksha! 🎉👶"
        def get_default_congratulations(*args, **kwargs):
            return "Congratulations on your delivery! Welcome to SantanRaksha! 🎉👶"

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
        
        mother_updated = False
        child_created = None
        
        # Use the atomic RPC function for improved performance
        try:
            # Prepare arguments for the RPC call
            rpc_params = {
                'p_mother_id': request.mother_id,
                'p_delivery_date': request.delivery_date.isoformat(),
                'p_delivery_type': request.delivery_type,
                'p_delivery_hospital': request.delivery_hospital,
                'p_delivery_complications': request.delivery_complications,
                'p_gestational_age_weeks': request.gestational_age_weeks
            }
            
            # Add child parameters if provided
            if request.child and request.child.name:
                rpc_params.update({
                    'p_child_name': request.child.name,
                    'p_child_gender': request.child.gender,
                    'p_birth_weight_kg': float(request.child.birth_weight_kg) if request.child.birth_weight_kg else None,
                    'p_birth_length_cm': float(request.child.birth_length_cm) if request.child.birth_length_cm else None,
                    'p_birth_head_circumference_cm': float(request.child.birth_head_circumference_cm) if request.child.birth_head_circumference_cm else None,
                    'p_apgar_score_1min': request.child.apgar_score_1min,
                    'p_apgar_score_5min': request.child.apgar_score_5min,
                    'p_birth_complications': request.child.birth_complications
                })
            
            # Execute RPC
            rpc_result = supabase.rpc('complete_delivery', rpc_params).execute()
            
            if rpc_result.data and len(rpc_result.data) > 0:
                result_data = rpc_result.data[0]
                mother_updated = result_data.get('mother_updated', False)
                child_created = result_data.get('child_created')
                
                logger.info(f"✅ RPC complete_delivery success for {request.mother_id}")
            else:
                 # Fallback to manual update if RPC fails or returns empty (should not happen if SQL is correct)
                 logger.warning("⚠️ RPC returned empty, falling back to manual update...")
                 # ... (fallback logic or just error out)
                 raise Exception("RPC returned no data")

        except Exception as rpc_error:
             logger.error(f"❌ RPC failed: {rpc_error}")
             # If RPC doesn't exist yet (user didn't run migration), we could fallback to manual
             # But for now, let's assume they ran it. If not, the error will guide them.
             raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(rpc_error)}")
        
        # Calculate days postpartum (fast, local)
        try:
            delivery_dt = request.delivery_date
            if delivery_dt.tzinfo is not None:
                delivery_dt = delivery_dt.replace(tzinfo=None)
            days_postpartum = max(0, (datetime.now() - delivery_dt).days)
        except Exception:
            days_postpartum = 0

        if mother_updated:
            # Generate personalized congratulations message
            try:
                # Fetch mother details for personalized message
                mother_details = supabase.table('mothers').select('name, preferred_language').eq('id', request.mother_id).single().execute()
                mother_name = mother_details.data.get('name', 'Mother') if mother_details.data else 'Mother'
                language = mother_details.data.get('preferred_language', 'en') if mother_details.data else 'en'
                
                # Generate congratulations
                congratulations = await generate_congratulations_message(
                    mother_name=mother_name,
                    child_name=request.child.name if request.child else None,
                    child_gender=request.child.gender if request.child else None,
                    delivery_type=request.delivery_type,
                    language=language
                )
                logger.info(f"✅ Generated congratulations for {mother_name}")
            except Exception as e:
                logger.warning(f"⚠️ Congratulations generation failed, using default: {e}")
                congratulations = get_default_congratulations(mother_name if 'mother_name' in locals() else "Mother", 
                                                              language if 'language' in locals() else "en")
            
            # Invalidate cache so lists update immediately
            invalidate_mothers_cache()
            
            return DeliveryCompletionResponse(
                success=True,
                message=congratulations,  # ✨ Personalized congratulations message!
                mother_updated=True,
                child_created=child_created,
                vaccination_schedule_created=True,
                active_system='santanraksha',
                days_postpartum=days_postpartum
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to Update mother record")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delivery completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Delivery completion failed: {str(e)}")


@router.get("/status/{mother_id}")
@cached(ttl_seconds=30, key_prefix="delivery:status")
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

@router.get("/children/{mother_id}")
async def get_mother_children_details(mother_id: str):
    """
    Get all children for a mother with their growth history.
    Used for the Growth Charts feature.
    """
    try:
        # 1. Fetch children
        # Try both 'children' and 'child' table names just in case, but migration said 'children'
        try:
            children_res = supabase.table('children').select('*').eq('mother_id', mother_id).execute()
        except Exception:
             # Fallback if table name differs
             children_res = supabase.table('child').select('*').eq('mother_id', mother_id).execute()
             
        if not children_res.data:
            return {"success": True, "children": []}
            
        children = children_res.data
        
        # 2. For each child, fetch growth records
        for child in children:
            child_id = child.get('id')
            try:
                growth_res = supabase.table('growth_records')\
                    .select('*')\
                    .eq('child_id', child_id)\
                    .order('measurement_date', desc=False)\
                    .execute()
                
                # Format for chart: { age_months, weight }
                # If we have birth_date, we can calculate age_months for every record
                records = growth_res.data or []
                
                # If records don't have age_months calculated, we might need to compute it
                # But let's assume records are raw.
                
                birth_date = datetime.fromisoformat(child['birth_date'].replace('Z', '+00:00')) if child.get('birth_date') else datetime.now()
                
                formatted_growth = []
                
                # Add birth weight as first point if exists
                if child.get('birth_weight_kg'):
                    formatted_growth.append({
                        "age_months": 0,
                        "weight": float(child['birth_weight_kg']),
                        "date": child['birth_date']
                    })
                    
                for rec in records:
                    # Calculate age in months at time of record
                    if rec.get('measurement_date'):
                        try:
                            m_date = datetime.fromisoformat(rec['measurement_date'].replace('Z', '+00:00'))
                            age_months = (m_date.year - birth_date.year) * 12 + (m_date.month - birth_date.month)
                            # Adjust slightly for days
                            if m_date.day < birth_date.day:
                                age_months -= 0.5
                            
                            age_months = max(0, round(age_months, 1))
                            
                            formatted_growth.append({
                                "age_months": age_months,
                                "weight": float(rec['weight_kg']),
                                "date": rec['measurement_date']
                            })
                        except Exception:
                            pass
                            
                # Sort by age
                formatted_growth.sort(key=lambda x: x['age_months'])
                child['growth_history'] = formatted_growth
                
            except Exception as gr_err:
                logger.warning(f"Could not fetch growth for child {child_id}: {gr_err}")
                child['growth_history'] = []
                
        return {"success": True, "children": children}

    except Exception as e:
        logger.error(f"Error fetching children details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
