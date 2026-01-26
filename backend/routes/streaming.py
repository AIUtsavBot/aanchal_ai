"""
Server-Sent Events (SSE) Streaming Routes
Real-time AI response streaming and progress updates
"""

import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stream", tags=["streaming"])


async def generate_sse_message(data: dict, event: str = "message") -> str:
    """Format data as SSE message"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("/ai-response/{session_id}")
async def stream_ai_response(
    session_id: str,
    query: str = Query(..., description="User query"),
    mother_id: Optional[str] = Query(None)
):
    """
    Stream AI response in real-time using Server-Sent Events
    
    - **session_id**: Session identifier
    - **query**: User's question
    - **mother_id**: Optional mother context
    """
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Send initial message
            yield await generate_sse_message({
                "type": "start",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get AI response (simulated streaming)
            response_text = await _get_ai_response(query, mother_id)
            
            # Stream response in chunks
            words = response_text.split()
            chunk_size = 5
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield await generate_sse_message({
                    "type": "chunk",
                    "content": chunk + " ",
                    "index": i // chunk_size
                })
                await asyncio.sleep(0.05)  # Smooth streaming effect
            
            # Send completion
            yield await generate_sse_message({
                "type": "complete",
                "session_id": session_id,
                "total_length": len(response_text)
            })
            
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            yield await generate_sse_message({
                "type": "error",
                "message": str(e)
            }, event="error")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/task-progress/{task_id}")
async def stream_task_progress(task_id: str):
    """
    Stream background task progress updates
    
    - **task_id**: Celery task ID
    """
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            from tasks.celery_app import celery_app
            
            max_wait = 300  # 5 minutes max
            check_interval = 1.0
            elapsed = 0
            
            while elapsed < max_wait:
                result = celery_app.AsyncResult(task_id)
                
                yield await generate_sse_message({
                    "type": "progress",
                    "task_id": task_id,
                    "status": result.status,
                    "ready": result.ready(),
                    "elapsed_seconds": elapsed
                })
                
                if result.ready():
                    if result.successful():
                        yield await generate_sse_message({
                            "type": "complete",
                            "task_id": task_id,
                            "result": result.result
                        })
                    else:
                        yield await generate_sse_message({
                            "type": "failed",
                            "task_id": task_id,
                            "error": str(result.result)
                        }, event="error")
                    break
                
                await asyncio.sleep(check_interval)
                elapsed += check_interval
            
            if elapsed >= max_wait:
                yield await generate_sse_message({
                    "type": "timeout",
                    "message": "Task monitoring timed out"
                })
                
        except ImportError:
            yield await generate_sse_message({
                "type": "error",
                "message": "Task queue not available"
            }, event="error")
        except Exception as e:
            logger.error(f"❌ Task progress error: {e}")
            yield await generate_sse_message({
                "type": "error",
                "message": str(e)
            }, event="error")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/data-export/{table_name}")
async def stream_data_export(
    table_name: str,
    format: str = Query("csv", regex="^(csv|json)$")
):
    """
    Stream large data exports
    
    - **table_name**: Table to export
    - **format**: Export format (csv, json)
    """
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            from services.async_db import async_db
            
            # Get data in batches
            batch_size = 100
            offset = 0
            total_rows = 0
            
            # Send header for CSV
            if format == "csv":
                # Fetch first row to get columns
                first_batch = await async_db.select(table_name, limit=1)
                if first_batch:
                    columns = list(first_batch[0].keys())
                    yield ",".join(columns) + "\n"
            
            while True:
                batch = await async_db.select(
                    table_name,
                    limit=batch_size,
                    offset=offset
                )
                
                if not batch:
                    break
                
                for row in batch:
                    if format == "csv":
                        values = [str(row.get(col, "")).replace(",", ";") for col in columns]
                        yield ",".join(values) + "\n"
                    else:
                        yield json.dumps(row) + "\n"
                
                total_rows += len(batch)
                offset += batch_size
                
                if len(batch) < batch_size:
                    break
            
            logger.info(f"📤 Exported {total_rows} rows from {table_name}")
            
        except Exception as e:
            logger.error(f"❌ Export error: {e}")
            yield f"ERROR: {e}\n"
    
    content_type = "text/csv" if format == "csv" else "application/x-ndjson"
    filename = f"{table_name}_export_{datetime.now().strftime('%Y%m%d')}.{format}"
    
    return StreamingResponse(
        generate(),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


async def _get_ai_response(query: str, mother_id: Optional[str]) -> str:
    """Get AI response for streaming"""
    try:
        # Try to use orchestrator
        try:
            from agents.orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
        except ImportError:
            orchestrator = None
        
        if orchestrator:
            context = {"mother_id": mother_id} if mother_id else {}
            return orchestrator.process_query(query, context, "stream_session")
        
        # Fallback to Gemini direct
        from google import genai
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            return "AI service not configured. Please set GEMINI_API_KEY."
        
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=query
        )
        return response.text
        
    except Exception as e:
        logger.error(f"❌ AI response error: {e}")
        return f"Sorry, I couldn't process your request: {e}"
