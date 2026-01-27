
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from routes.auth_routes import get_current_user, require_admin
from services.ai_prediction_service import AIPredictionService

# Try to get gemini from main (dependency injection pattern usually better, but keeping simple)
try:
    from google import genai
    import os
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
except:
    gemini_client = None

# Import Supabase
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])
logger = logging.getLogger(__name__)

@router.post("/analyze/{mother_id}")
async def trigger_risk_analysis(mother_id: str, current_user: dict = Depends(get_current_user)):
    """
    Trigger a fresh AI Risk Analysis for a mother.
    """
    try:
        result = await AIPredictionService.analyze_mother_risk(mother_id)
        return {"success": True, "insight": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary/{mother_id}")
async def generate_summary(mother_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate a GenAI Health Summary.
    """
    if not gemini_client:
        raise HTTPException(status_code=503, detail="AI Service Integration unavailable")
        
    try:
        result = await AIPredictionService.generate_health_summary(mother_id, gemini_client)
        return {"success": True, "insight": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{mother_id}")
async def get_patient_insights(mother_id: str, type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """
    Get historical AI insights for a patient.
    """
    try:
        query = supabase.table("patient_insights").select("*").eq("mother_id", mother_id).order("generated_at", desc=True)
        
        if type:
            query = query.eq("type", type)
            
        result = query.limit(20).execute()
        
        return {"success": True, "insights": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
