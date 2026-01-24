"""
MatruRaksha AI - Offline Sync Routes
Handles batch sync of data queued while offline
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/sync", tags=["Offline Sync"])

# Try to import auth middleware
try:
    from backend.middleware.auth import get_current_user
except ImportError:
    from middleware.auth import get_current_user

# Try to import database service
try:
    from backend.services.supabase_service import supabase, DatabaseService
except ImportError:
    from services.supabase_service import supabase, DatabaseService


# ==================== PYDANTIC MODELS ====================

class PendingForm(BaseModel):
    """A form that was queued while offline"""
    form_type: str
    form_data: dict
    created_at: str
    offline_id: Optional[int] = None


class PendingChat(BaseModel):
    """A chat message that was queued while offline"""
    mother_id: str
    message: str
    metadata: Optional[dict] = {}
    created_at: str
    offline_id: Optional[int] = None


class PendingDocument(BaseModel):
    """A document that was queued while offline"""
    mother_id: str
    file_name: str
    file_type: str
    file_data: str  # Base64 encoded
    document_type: str
    created_at: str
    offline_id: Optional[int] = None


class BatchSyncRequest(BaseModel):
    """Request for batch sync of multiple items"""
    forms: Optional[List[PendingForm]] = []
    chats: Optional[List[PendingChat]] = []
    documents: Optional[List[PendingDocument]] = []


class SyncResult(BaseModel):
    """Result of a single sync operation"""
    offline_id: Optional[int]
    success: bool
    server_id: Optional[str] = None
    error: Optional[str] = None


class BatchSyncResponse(BaseModel):
    """Response for batch sync"""
    forms: List[SyncResult]
    chats: List[SyncResult]
    documents: List[SyncResult]
    summary: dict


# ==================== ROUTES ====================

@router.post("/batch", response_model=BatchSyncResponse)
async def batch_sync(
    request: BatchSyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Batch sync all pending offline data.
    
    This endpoint processes:
    - Pending form submissions
    - Pending chat messages
    - Pending document uploads
    
    Returns results for each item indicating success/failure.
    """
    logger.info(f"📥 Batch sync request: {len(request.forms)} forms, "
                f"{len(request.chats)} chats, {len(request.documents)} documents")
    
    results = {
        "forms": [],
        "chats": [],
        "documents": []
    }
    
    # Process forms
    for form in request.forms or []:
        result = await _sync_form(form)
        results["forms"].append(result)
    
    # Process chats
    for chat in request.chats or []:
        result = await _sync_chat(chat)
        results["chats"].append(result)
    
    # Process documents
    for doc in request.documents or []:
        result = await _sync_document(doc)
        results["documents"].append(result)
    
    # Build summary
    summary = {
        "total_received": len(request.forms or []) + len(request.chats or []) + len(request.documents or []),
        "forms_synced": sum(1 for r in results["forms"] if r.success),
        "forms_failed": sum(1 for r in results["forms"] if not r.success),
        "chats_synced": sum(1 for r in results["chats"] if r.success),
        "chats_failed": sum(1 for r in results["chats"] if not r.success),
        "documents_synced": sum(1 for r in results["documents"] if r.success),
        "documents_failed": sum(1 for r in results["documents"] if not r.success),
        "synced_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"✅ Batch sync complete: {summary}")
    
    return BatchSyncResponse(
        forms=results["forms"],
        chats=results["chats"],
        documents=results["documents"],
        summary=summary
    )


@router.post("/forms", response_model=List[SyncResult])
async def sync_forms(
    forms: List[PendingForm],
    current_user: dict = Depends(get_current_user)
):
    """Sync pending forms only"""
    results = []
    for form in forms:
        result = await _sync_form(form)
        results.append(result)
    return results


@router.post("/chats", response_model=List[SyncResult])
async def sync_chats(
    chats: List[PendingChat],
    current_user: dict = Depends(get_current_user)
):
    """Sync pending chats only"""
    results = []
    for chat in chats:
        result = await _sync_chat(chat)
        results.append(result)
    return results


@router.post("/documents", response_model=List[SyncResult])
async def sync_documents(
    documents: List[PendingDocument],
    current_user: dict = Depends(get_current_user)
):
    """Sync pending documents only"""
    results = []
    for doc in documents:
        result = await _sync_document(doc)
        results.append(result)
    return results


@router.get("/status")
async def get_sync_status(current_user: dict = Depends(get_current_user)):
    """Get sync service status"""
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": supabase is not None
    }


# ==================== HELPER FUNCTIONS ====================

async def _sync_form(form: PendingForm) -> SyncResult:
    """Sync a single form to the database"""
    try:
        form_type = form.form_type
        form_data = form.form_data
        
        # Route based on form type
        if form_type == "mother_registration":
            # Insert into mothers table
            result = supabase.table("mothers").insert(form_data).execute()
            server_id = result.data[0]["id"] if result.data else None
            
        elif form_type == "health_checkin":
            # Insert into health_timeline table
            result = supabase.table("health_timeline").insert(form_data).execute()
            server_id = result.data[0]["id"] if result.data else None
            
        elif form_type == "risk_assessment":
            # Insert into risk_assessments table
            result = supabase.table("risk_assessments").insert(form_data).execute()
            server_id = result.data[0]["id"] if result.data else None
            
        else:
            # Generic insert - try to use form_type as table name
            result = supabase.table(form_type).insert(form_data).execute()
            server_id = result.data[0]["id"] if result.data else None
        
        return SyncResult(
            offline_id=form.offline_id,
            success=True,
            server_id=str(server_id) if server_id else None
        )
        
    except Exception as e:
        logger.error(f"Form sync error: {e}")
        return SyncResult(
            offline_id=form.offline_id,
            success=False,
            error=str(e)
        )


async def _sync_chat(chat: PendingChat) -> SyncResult:
    """Sync a single chat message"""
    try:
        # Store chat in telegram_logs or chat_history table
        chat_data = {
            "mother_id": chat.mother_id,
            "message_type": "user",
            "message_content": chat.message,
            "status": "synced_offline",
            "created_at": chat.created_at
        }
        
        result = supabase.table("telegram_logs").insert(chat_data).execute()
        server_id = result.data[0]["id"] if result.data else None
        
        return SyncResult(
            offline_id=chat.offline_id,
            success=True,
            server_id=str(server_id) if server_id else None
        )
        
    except Exception as e:
        logger.error(f"Chat sync error: {e}")
        return SyncResult(
            offline_id=chat.offline_id,
            success=False,
            error=str(e)
        )


async def _sync_document(doc: PendingDocument) -> SyncResult:
    """Sync a single document"""
    try:
        import base64
        
        # Decode base64 file data
        if "," in doc.file_data:
            file_data = doc.file_data.split(",")[1]
        else:
            file_data = doc.file_data
        
        file_bytes = base64.b64decode(file_data)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        storage_path = f"documents/{doc.mother_id}/{timestamp}_{doc.file_name}"
        
        # Upload to Supabase storage
        supabase.storage.from_("medical-documents").upload(
            storage_path,
            file_bytes,
            file_options={"content-type": doc.file_type}
        )
        
        # Get public URL
        file_url = supabase.storage.from_("medical-documents").get_public_url(storage_path)
        
        # Create medical report record
        report_data = {
            "mother_id": doc.mother_id,
            "filename": doc.file_name,
            "file_url": file_url,
            "file_type": doc.document_type,
            "analysis_status": "pending",
            "uploaded_at": doc.created_at
        }
        
        result = supabase.table("medical_reports").insert(report_data).execute()
        server_id = result.data[0]["id"] if result.data else None
        
        return SyncResult(
            offline_id=doc.offline_id,
            success=True,
            server_id=str(server_id) if server_id else None
        )
        
    except Exception as e:
        logger.error(f"Document sync error: {e}")
        return SyncResult(
            offline_id=doc.offline_id,
            success=False,
            error=str(e)
        )
