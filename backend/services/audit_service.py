
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

# Try to import supabase
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class AuditService:
    """
    Service for securely logging critical system actions.
    Designed to be fire-and-forget (async) so it doesn't slow down the main request.
    """
    
    @staticmethod
    async def log_action(
        action: str,
        request: Optional[Request] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        target_resource: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None
    ):
        """
        Log an audit event securely.
        """
        try:
            # Extract info from request if provided
            client_ip = ip_address
            user_agent = None
            
            if request:
                if not client_ip:
                    client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
            # Construct log entry
            log_entry = {
                "action": action,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "target_resource": target_resource,
                "target_id": target_id,
                "details": details or {},
                "ip_address": client_ip,
                "user_agent": user_agent,
                "status": status,
                "created_at": datetime.now().isoformat()
            }
            
            # Fire and forget - use create_task to run in background
            # We don't want audit logging to block the user response
            asyncio.create_task(AuditService._persist_log(log_entry))
            
        except Exception as e:
            # Fallback logging to file/stdout if DB fails
            logger.error(f"Failed to initiate audit log: {e}")
            logger.critical(f"AUDIT_FAILURE: {action} by {actor_id} - {status}")

    @staticmethod
    async def _persist_log(entry: Dict[str, Any]):
        """Internal method to save log to database"""
        try:
            supabase.table("audit_logs").insert(entry).execute()
        except Exception as e:
            logger.error(f"CRITICAL: Failed to write audit log to DB: {e}")
            logger.error(f"LOST_AUDIT_LOG: {entry}")

# Helper decorator for auditing route access
def audit_action(action_name: str, resource: str):
    """
    Decorator to automatically audit route access.
    Usage:
        @router.get("/{id}")
        @audit_action("VIEW_RECORD", "mothers")
        async def get_mother(id: str, request: Request, current_user: dict = Depends(get_current_user)):
            ...
    NOTE: Requires request and current_user in endpoint arguments
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract common dependencies
            request = kwargs.get('request')
            # Try to find request in args if not in kwargs (FastAPI usually passes as kwarg)
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            current_user = kwargs.get('current_user')
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                if current_user:
                    actor_id = current_user.get("id") or current_user.get("user_id")
                    actor_role = current_user.get("role")
                    
                    # Try to find target_id from kwargs
                    target_id = None
                    for k, v in kwargs.items():
                        if k.endswith("_id") or k == "id":
                            target_id = str(v)
                            break
                    
                    await AuditService.log_action(
                        action=action_name,
                        request=request,
                        actor_id=actor_id,
                        actor_role=actor_role,
                        target_resource=resource,
                        target_id=target_id,
                        status="SUCCESS"
                    )
                return result
                
            except Exception as e:
                # Log failure
                if current_user:
                    actor_id = current_user.get("id") or current_user.get("user_id")
                    actor_role = current_user.get("role")
                    
                    await AuditService.log_action(
                        action=action_name,
                        request=request,
                        actor_id=actor_id,
                        actor_role=actor_role,
                        target_resource=resource,
                        status="FAILURE",
                        details={"error": str(e)}
                    )
                raise e
                
        return wrapper
    return decorator
