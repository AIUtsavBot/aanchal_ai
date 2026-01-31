
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from services.auth_service import get_current_user
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

class WebhookCreate(BaseModel):
    url: str
    events: List[str]
    description: Optional[str] = None
    secret: Optional[str] = None # Optional, if not provided will generate

class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: str

@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: dict = Depends(get_current_user)
):
    """Register a new webhook endpoint"""
    # Only admin should allow this
    if current_user.get("role") != "ADMIN":
        raise HTTPException(403, "Only admins can manage webhooks")
        
    try:
        data = webhook.dict()
        if not data.get("secret"):
            data["secret"] = uuid.uuid4().hex
        
        data["created_by"] = current_user.get("id")
        
        result = supabase.table("webhooks").insert(data).execute()
        
        if result.data:
            return result.data[0]
        raise HTTPException(500, "Failed to create webhook")
        
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(500, str(e))

@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """List all webhooks"""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(403, "Unauthorized")
        
    res = supabase.table("webhooks").select("*").limit(100).execute()
    return res.data or []

@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a webhook"""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(403, "Unauthorized")
        
    supabase.table("webhooks").delete().eq("id", webhook_id).execute()
    return {"success": True}
