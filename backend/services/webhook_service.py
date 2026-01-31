
import logging
import hmac
import hashlib
import json
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from services.supabase_service import supabase

logger = logging.getLogger(__name__)

class WebhookService:
    """Service to manage and dispatch webhooks"""
    
    @staticmethod
    async def trigger_event(event_name: str, payload: Dict[str, Any]):
        """Trigger a webhook event to all subscribed endpoints"""
        try:
            # Get active webhooks for this event
            # Using contains operator for array
            response = supabase.table("webhooks") \
                .select("*") \
                .eq("is_active", True) \
                .cs("events", [event_name]) \
                .execute()
                
            webhooks = response.data or []
            
            if not webhooks:
                logger.debug(f"No webhooks found for event: {event_name}")
                return
            
            logger.info(f"Dispatching event '{event_name}' to {len(webhooks)} webhooks")
            
            # Dispatch in background
            asyncio.create_task(WebhookService._dispatch_batch(webhooks, event_name, payload))
            
        except Exception as e:
            logger.error(f"Error triggering webhook event: {e}")

    @staticmethod
    async def _dispatch_batch(webhooks: List[dict], event_name: str, payload: Dict[str, Any]):
        """Dispatch to multiple webhooks concurrently"""
        tasks = []
        for wh in webhooks:
            tasks.append(WebhookService._dispatch_single(wh, event_name, payload))
        await asyncio.gather(*tasks)

    @staticmethod
    async def _dispatch_single(webhook: dict, event_name: str, payload: Dict[str, Any]):
        """Send single webhook request with retries"""
        url = webhook.get("url")
        secret = webhook.get("secret")
        webhook_id = webhook.get("id")
        
        # Prepare payload
        data = {
            "id": f"evt_{int(datetime.now().timestamp())}",
            "event": event_name,
            "created_at": datetime.utcnow().isoformat(),
            "data": payload
        }
        json_data = json.dumps(data)
        
        # Sign payload
        signature = hmac.new(
            secret.encode(),
            json_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-MatruRaksha-Event": event_name,
            "X-MatruRaksha-Signature": signature,
            "User-Agent": "MatruRaksha-Webhook/1.0"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, content=json_data, headers=headers)
                status_code = response.status_code
                response_text = response.text[:1000] # truncate
                
                # Log Result
                try:
                    supabase.table("webhook_logs").insert({
                        "webhook_id": webhook_id,
                        "event": event_name,
                        "status": status_code,
                        "response": response_text,
                        "payload": data
                    }).execute()
                except Exception:
                    pass
                    
                if status_code >= 400:
                    logger.warning(f"Webhook {webhook_id} failed with {status_code}")
                else:
                    logger.info(f"Webhook {webhook_id} delivered successfully")
                    
        except Exception as e:
            logger.error(f"Failed to send webhook {webhook_id}: {e}")
            # Try to log failure
            try:
                supabase.table("webhook_logs").insert({
                    "webhook_id": webhook_id,
                    "event": event_name,
                    "status": 0,
                    "response": str(e),
                    "payload": data
                }).execute()
            except Exception:
                pass
