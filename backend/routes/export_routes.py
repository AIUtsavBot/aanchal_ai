
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
try:
    from middleware.auth import get_current_user
except ImportError:
    from backend.middleware.auth import get_current_user
from services.export_service import ExportService
# Use cache service if available, though exports might be fresh
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["Data Export"])

@router.get("/vaccination/{child_id}/pdf")
async def export_vaccinations_pdf(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export child vaccination record as PDF"""
    try:
        # Get child info
        child_res = supabase.table("children").select("*").eq("id", child_id).single().execute()
        if not child_res.data:
            raise HTTPException(404, "Child not found")
        
        # Get vaccinations
        vac_res = supabase.table("vaccinations").select("*").eq("child_id", child_id).order("due_date").limit(100).execute()
        
        pdf_buffer = ExportService.generate_vaccination_pdf(child_res.data, vac_res.data or [])
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=vaccinations_{child_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(500, f"Export failed: {e}")

@router.get("/vaccination/{child_id}/csv")
async def export_vaccinations_csv(
    child_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export child vaccination record as CSV"""
    try:
        vac_res = supabase.table("vaccinations").select("*").eq("child_id", child_id).limit(100).execute()
        data = vac_res.data or []
        
        if not data:
            return StreamingResponse(iter(["No data"]), media_type="text/csv")
            
        csv_buffer = ExportService.generate_csv_export(data, list(data[0].keys()))
        
        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=vaccinations_{child_id}.csv"}
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(500, f"Export failed: {e}")
