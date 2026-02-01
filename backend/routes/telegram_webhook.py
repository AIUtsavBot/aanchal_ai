"""
Telegram Webhook Route
Endpoint to receive updates from Telegram when running in webhook mode
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from telegram import Update
import os

# Import the global bot application from main (will need to avoid circular imports)
# We will use a dependency injection pattern or import inside function

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])

@router.post("/webhook/{token}", include_in_schema=False)
async def telegram_webhook(token: str, request: Request):
    """
    Handle incoming Telegram updates
    This endpoint is called by Telegram servers
    """
    # 1. Validate Token
    expected_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not expected_token or token != expected_token:
        logger.warning(f"⚠️  Unauthorized webhook attempt with token: {token[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram Token"
        )

    # 2. Get Application Instance
    # We need to get the application instance that was initialized in main.py
    # Since we can't easily import it due to circular deps, we can look it up
    # or rely on it being set in the module if we did a specific pattern.
    # A cleaner way in FastAPI is to store it on app.state, but accessing `app` here is tricky.
    # For now, we will try to import it from main, handling the circular import.
    
    try:
        from backend.main import telegram_bot_app
    except ImportError:
        try:
            from main import telegram_bot_app
        except ImportError:
            logger.error("❌ Could not import telegram_bot_app from main")
            raise HTTPException(status_code=500, detail="Bot not initialized")
            
    if not telegram_bot_app:
        logger.error("❌ Telegram Bot App is None (not initialized)")
        raise HTTPException(status_code=503, detail="Bot system not ready")

    # 3. Process Update
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_bot_app.bot)
        
        # Feed update to the application
        # await telegram_bot_app.process_update(update) is for PTB v13, v20+ uses update_queue
        
        if hasattr(telegram_bot_app, 'update_queue'):
            await telegram_bot_app.update_queue.put(update)
        else:
            # Fallback for older versions or if using a different method
            # For python-telegram-bot v20+, the standard way in webhook mode 
            # is properly feeding the update queue.
             await telegram_bot_app.process_update(update)

        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook update: {e}")
        # Return 200 to Telegram so they don't keep retrying and flooding us
        return {"status": "error", "message": str(e)}
