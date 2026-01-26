"""
Background Task API Routes
Endpoints for managing and monitoring background tasks
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["background-tasks"])


class TaskSubmitRequest(BaseModel):
    """Request model for submitting tasks"""
    task_type: str
    params: Dict[str, Any] = {}


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a background task
    
    - **task_id**: Celery task ID
    """
    try:
        from tasks.celery_app import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        return TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            ready=result.ready(),
            successful=result.successful() if result.ready() else None,
            result=result.result if result.ready() and result.successful() else None,
            error=str(result.result) if result.ready() and not result.successful() else None
        )
        
    except ImportError:
        raise HTTPException(503, "Task queue not available")
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(500, str(e))


@router.post("/submit/risk-analysis")
async def submit_risk_analysis(
    mother_id: str = Query(...),
    assessment_data: Dict[str, Any] = {}
):
    """Submit risk analysis task"""
    try:
        from tasks.ai_tasks import analyze_risk_async
        
        task = analyze_risk_async.delay(mother_id, assessment_data)
        logger.info(f"🚀 Risk analysis task submitted: {task.id}")
        
        return {"task_id": task.id, "status": "submitted", "mother_id": mother_id}
        
    except ImportError:
        raise HTTPException(503, "Task queue not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/submit/report")
async def submit_report_generation(
    mother_id: str = Query(...)
):
    """Submit report generation task"""
    try:
        from tasks.report_tasks import generate_postnatal_report_async
        
        task = generate_postnatal_report_async.delay(mother_id)
        logger.info(f"📄 Report task submitted: {task.id}")
        
        return {"task_id": task.id, "status": "submitted", "mother_id": mother_id}
        
    except ImportError:
        raise HTTPException(503, "Task queue not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/submit/notification")
async def submit_notification(
    notification_type: str = Query(..., regex="^(email|sms|telegram)$"),
    recipient: str = Query(...),
    message: str = Query(...),
    subject: Optional[str] = Query(None)
):
    """Submit notification task"""
    try:
        from tasks.notification_tasks import send_email_async, send_sms_async, send_telegram_async
        
        if notification_type == "email":
            task = send_email_async.delay(recipient, subject or "Notification", message)
        elif notification_type == "sms":
            task = send_sms_async.delay(recipient, message)
        else:
            task = send_telegram_async.delay(recipient, message)
        
        logger.info(f"📬 Notification task submitted: {task.id}")
        
        return {"task_id": task.id, "status": "submitted", "type": notification_type}
        
    except ImportError:
        raise HTTPException(503, "Task queue not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/{task_id}")
async def revoke_task(task_id: str, terminate: bool = Query(False)):
    """Revoke/cancel a pending task"""
    try:
        from tasks.celery_app import celery_app
        
        celery_app.control.revoke(task_id, terminate=terminate)
        logger.info(f"🛑 Task revoked: {task_id}")
        
        return {"task_id": task_id, "status": "revoked", "terminated": terminate}
        
    except ImportError:
        raise HTTPException(503, "Task queue not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/queue/stats")
async def get_queue_stats():
    """Get background task queue statistics"""
    try:
        from tasks.celery_app import celery_app
        
        inspect = celery_app.control.inspect()
        
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        scheduled = inspect.scheduled() or {}
        
        total_active = sum(len(v) for v in active.values())
        total_reserved = sum(len(v) for v in reserved.values())
        total_scheduled = sum(len(v) for v in scheduled.values())
        
        return {
            "status": "connected",
            "workers": list(active.keys()),
            "active_tasks": total_active,
            "reserved_tasks": total_reserved,
            "scheduled_tasks": total_scheduled
        }
        
    except ImportError:
        return {"status": "not_available", "message": "Celery not installed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
