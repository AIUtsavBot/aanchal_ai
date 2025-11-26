"""
MatruRaksha AI - Enhanced API Endpoints
File: backend/enhanced_api.py

New endpoints for:
- Report analysis and storage
- Context memory management
- Health timeline tracking
- Conversation history
- Agent creation and queries
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
try:
    from backend.context_builder import build_holistic_context
except ImportError:
    from context_builder import build_holistic_context

# Load environment
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["Enhanced Features"])

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to import Contextual AI (optional)
try:
    from contextual import ContextualAI
    CONTEXTUAL_API_KEY = os.getenv("CONTEXTUAL_API_KEY")
    contextual_client = ContextualAI(api_key=CONTEXTUAL_API_KEY)
    CONTEXTUAL_AVAILABLE = True
    logger.info("✅ Contextual AI available in enhanced_api")
except Exception as e:
    logger.warning(f"⚠️  Contextual AI not available: {e}")
    contextual_client = None
    CONTEXTUAL_AVAILABLE = False


# ==================== PYDANTIC MODELS ====================

class ReportAnalysis(BaseModel):
    mother_id: int
    filename: str
    analysis_summary: str
    health_metrics: Dict[str, Any]
    concerns: List[str]
    recommendations: List[str]
    datastore_id: Optional[str] = None
    document_id: Optional[str] = None


class ContextMemory(BaseModel):
    mother_id: int
    memory_key: str
    memory_value: str
    memory_type: str = "fact"
    source: str = "conversation"


class HealthTimelineEvent(BaseModel):
    mother_id: int
    event_date: str
    event_type: str
    event_data: Dict[str, Any]
    blood_pressure: Optional[str] = None
    hemoglobin: Optional[float] = None
    sugar_level: Optional[float] = None
    weight: Optional[float] = None
    summary: Optional[str] = None
    concerns: Optional[List[str]] = None


class ConversationMessage(BaseModel):
    mother_id: int
    message_role: str
    message_content: str
    context_used: Optional[List[str]] = None
    agent_response: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    mother_id: int
    query: str
    use_context: bool = True
    language: Optional[str] = "en"

#


# ==================== HELPER FUNCTIONS ====================

async def store_context_memory(
    mother_id: int,
    key: str,
    value: str,
    memory_type: str = "fact",
    source: str = "system"
):
    """Helper to store context memory"""
    try:
        # Try to use RPC function if exists, otherwise insert directly
        try:
            supabase.rpc('store_memory', {
                'mother_id_param': mother_id,
                'key_param': key,
                'value_param': value,
                'type_param': memory_type,
                'source_param': source
            }).execute()
        except:
            # Fallback to direct insert
            supabase.table("context_memory").insert({
                "mother_id": mother_id,
                "memory_key": key,
                "memory_value": value,
                "memory_type": memory_type,
                "source": source
            }).execute()
    except Exception as e:
        logger.error(f"Error storing context memory: {e}")


# ==================== REPORT ENDPOINTS ====================

@router.post("/reports/analyze")
async def store_report_analysis(analysis: ReportAnalysis):
    """Store analyzed medical report"""
    try:
        result = supabase.table("medical_reports").insert({
            "mother_id": analysis.mother_id,
            "filename": analysis.filename,
            "upload_date": datetime.now().isoformat(),
            "analysis_summary": analysis.analysis_summary,
            "health_metrics": json.dumps(analysis.health_metrics),
            "concerns": json.dumps(analysis.concerns),
            "recommendations": json.dumps(analysis.recommendations),
            "datastore_id": analysis.datastore_id,
            "document_id": analysis.document_id,
            "processed": True
        }).execute()
        
        # Store key metrics in context memory
        for key, value in analysis.health_metrics.items():
            await store_context_memory(
                analysis.mother_id,
                f"metric_{key}",
                str(value),
                "health_metric",
                "report"
            )
        
        # Store concerns in memory
        for concern in analysis.concerns:
            await store_context_memory(
                analysis.mother_id,
                f"concern_{datetime.now().isoformat()}",
                concern,
                "concern",
                "report"
            )
        
        return {"success": True, "report_id": result.data[0]['id']}
    
    except Exception as e:
        logger.error(f"Error storing report analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/mother/{mother_id}")
async def get_mother_reports(mother_id: int, limit: int = 10):
    """Get all reports for a mother"""
    try:
        response = supabase.table("medical_reports")\
            .select("*")\
            .eq("mother_id", mother_id)\
            .order("uploaded_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {"success": True, "reports": response.data}
    
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MEMORY ENDPOINTS ====================

@router.post("/memory/store")
async def store_memory_endpoint(memory: ContextMemory):
    """Store context memory"""
    try:
        await store_context_memory(
            memory.mother_id,
            memory.memory_key,
            memory.memory_value,
            memory.memory_type,
            memory.source
        )
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/retrieve/{mother_id}")
async def retrieve_memory(mother_id: str, limit: int = 20):
    """Retrieve relevant memories for a mother - accepts UUID or integer ID"""
    try:
        # Try to use RPC function if exists
        try:
            response = supabase.rpc('get_relevant_memories', {
                'mother_id_param': mother_id,
                'limit_param': limit
            }).execute()
        except:
            # Fallback to direct query
            response = supabase.table("context_memory")\
                .select("*")\
                .eq("mother_id", mother_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
        
        return {"success": True, "memories": response.data}
    
    except Exception as e:
        logger.error(f"Error retrieving memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIMELINE ENDPOINTS ====================

@router.post("/timeline/event")
async def add_timeline_event(event: HealthTimelineEvent):
    """Add event to health timeline"""
    try:
        result = supabase.table("health_timeline").insert({
            "mother_id": event.mother_id,
            "event_date": event.event_date,
            "event_type": event.event_type,
            "event_data": json.dumps(event.event_data),
            "blood_pressure": event.blood_pressure,
            "hemoglobin": event.hemoglobin,
            "sugar_level": event.sugar_level,
            "weight": event.weight,
            "summary": event.summary,
            "concerns": json.dumps(event.concerns or [])
        }).execute()
        
        return {"success": True, "event_id": result.data[0]['id']}
    
    except Exception as e:
        logger.error(f"Error adding timeline event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{mother_id}")
async def get_timeline(mother_id: str, limit: int = 50):
    """Get health timeline for a mother - accepts UUID or integer ID"""
    try:
        # Try different possible column names for date ordering
        date_columns = ["event_date", "date", "created_at"]
        response = None
        last_error = None
        
        for date_col in date_columns:
            try:
                response = supabase.table("health_timeline")\
                    .select("*")\
                    .eq("mother_id", mother_id)\
                    .order(date_col, desc=True)\
                    .limit(limit)\
                    .execute()
                logger.info(f"Successfully retrieved timeline using column: {date_col}")
                break
            except Exception as col_error:
                last_error = col_error
                logger.debug(f"Column {date_col} not available, trying next...")
                continue
        
        # If all date columns failed, try without ordering
        if not response:
            try:
                response = supabase.table("health_timeline")\
                    .select("*")\
                    .eq("mother_id", mother_id)\
                    .limit(limit)\
                    .execute()
                logger.info("Retrieved timeline without date ordering")
            except Exception as e:
                logger.error(f"Error getting timeline (all methods failed): {e}")
                # Return empty timeline instead of raising error
                return {"success": True, "timeline": []}
        
        return {"success": True, "timeline": response.data if response else []}
    
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        # Return empty timeline instead of raising error to prevent summary endpoint failure
        return {"success": True, "timeline": []}


# ==================== CONVERSATION ENDPOINTS ====================

@router.post("/conversation/message")
async def store_conversation(message: ConversationMessage):
    """Store conversation message"""
    try:
        result = supabase.table("conversations").insert({
            "mother_id": message.mother_id,
            "message_role": message.message_role,
            "message_content": message.message_content,
            "context_used": json.dumps(message.context_used or []),
            "agent_response": json.dumps(message.agent_response or {})
        }).execute()
        
        return {"success": True, "message_id": result.data[0]['id']}
    
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{mother_id}")
async def get_conversation_history(mother_id: str, limit: int = 50):
    """Get conversation history - accepts UUID or integer ID"""
    try:
        response = supabase.table("conversations")\
            .select("*")\
            .eq("mother_id", mother_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        # Reverse to get chronological order
        return {"success": True, "messages": list(reversed(response.data))}
    
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 

# ==================== SUMMARY ENDPOINT ====================

@router.get("/summary/{mother_id}")
async def get_health_summary(mother_id: str):
    """Get comprehensive health summary - accepts UUID or integer ID"""
    try:
        # Try to use SQL function if exists
        try:
            summary = supabase.rpc('get_health_summary', {
                'mother_id_param': mother_id
            }).execute()
            summary_data = summary.data
        except Exception as rpc_error:
            logger.warning(f"RPC function not available: {rpc_error}")
            # Fallback to manual aggregation
            summary_data = {"message": "Summary function not available"}
        
        # Get latest timeline events (with error handling)
        timeline = {"success": True, "timeline": []}
        try:
            timeline = await get_timeline(mother_id, limit=5)
        except Exception as timeline_error:
            logger.warning(f"Could not retrieve timeline: {timeline_error}")
            timeline = {"success": True, "timeline": []}
        
        # Get recent memories (with error handling)
        memories = {"success": True, "memories": []}
        try:
            memories = await retrieve_memory(mother_id, limit=10)
        except Exception as memory_error:
            logger.warning(f"Could not retrieve memories: {memory_error}")
            memories = {"success": True, "memories": []}
        
        # Get mother details
        mother = None
        try:
            mother_result = supabase.table("mothers").select("*").eq("id", mother_id).execute()
            mother = mother_result.data[0] if mother_result.data else None
        except Exception as mother_error:
            logger.warning(f"Could not retrieve mother details: {mother_error}")
        
        return {
            "success": True,
            "mother": mother,
            "summary": summary_data,
            "recent_timeline": timeline.get("timeline", []),
            "key_memories": memories.get("memories", [])
        }
    
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AGENT ENDPOINTS ====================

@router.post("/agent/query")
async def query_agent_with_context(request: QueryRequest):
    """Query agent with context awareness"""
    try:
        mother_id = request.mother_id
        query = request.query
        language = getattr(request, "language", "en")
        
        # Get agent config
        agent_config = supabase.table("agent_configs")\
            .select("*")\
            .eq("mother_id", mother_id)\
            .execute()
        if not agent_config.data:
            raise HTTPException(status_code=404, detail="Agent not configured for this user")
        agent_id = agent_config.data[0]['agent_id']
        # Build holistic context
        context_items = []
        context_str = ""
        if request.use_context:
            context_result = build_holistic_context(mother_id, supabase)
            context_str = context_result.get("context_text", "")
            context_items = context_result.get("sources", [])
        # Query the agent if available
        if CONTEXTUAL_AVAILABLE and contextual_client:
            full_query = f"Respond in language: {language}.\n{context_str}\n\nUser question: {query}"
            response = contextual_client.agents.query.create(
                agent_id=agent_id,
                messages=[{"role": "user", "content": full_query}]
            )
            answer = response.content if hasattr(response, 'content') else str(response)
        else:
            answer = f"Context-aware response to: {query}\n\nAgent AI not available. Using basic response."
        # Store conversation
        await store_conversation(ConversationMessage(
            mother_id=mother_id,
            message_role="user",
            message_content=query,
            context_used=[str(c) for c in context_items[:5]]
        ))
        await store_conversation(ConversationMessage(
            mother_id=mother_id,
            message_role="assistant",
            message_content=answer
        ))
        return {
            "success": True,
            "answer": answer,
            "context_used": len(context_items)
        }
    except Exception as e:
        logger.error(f"Error querying agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/create")
async def create_agent_for_mother(mother_id: int):
    """Create Contextual AI agent for a mother"""
    
    if not CONTEXTUAL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Contextual AI not available"
        )
    
    try:
        # Get mother details
        mother = supabase.table("mothers").select("*").eq("id", mother_id).execute()
        if not mother.data:
            raise HTTPException(status_code=404, detail="Mother not found")
        
        mother_data = mother.data[0]
        name = mother_data['name']
        
        # Create datastore
        datastore = contextual_client.datastores.create(
            name=f"matruraksha_{mother_id}_{name}"
        )
        
        # Create agent with personalized prompt
        system_prompt = f"""You are MatruRaksha AI, a personalized maternal health assistant for {name}.

Your role is to:
1. Analyze medical reports and extract key health information
2. Monitor pregnancy health trends over time
3. Provide personalized health advice based on uploaded reports and medical history
4. Alert about potential risks based on extracted metrics
5. Answer health questions using the mother's complete medical context

Always be empathetic, supportive, and encouraging. Prioritize {name}'s wellbeing.
Use the context provided from previous reports and conversations to give personalized responses.

Mother's profile:
- Age: {mother_data.get('age', 'N/A')}
- Gravida: {mother_data.get('gravida', 'N/A')}
- Location: {mother_data.get('location', 'N/A')}
"""
        
        agent = contextual_client.agents.create(
            name=f"MatruRaksha_Agent_{mother_id}",
            description=f"Personal health assistant for {name}",
            datastore_ids=[datastore.id],
            system_prompt=system_prompt
        )
        
        # Store configuration
        supabase.table("agent_configs").insert({
            "mother_id": mother_id,
            "datastore_id": datastore.id,
            "agent_id": agent.id,
            "system_prompt": system_prompt,
            "active": True
        }).execute()
        
        return {
            "success": True,
            "datastore_id": datastore.id,
            "agent_id": agent.id
        }
    
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECK ====================

@router.get("/health")
def enhanced_api_health():
    """Health check for enhanced API"""
    return {
        "status": "healthy",
        "service": "Enhanced API",
        "contextual_ai": "available" if CONTEXTUAL_AVAILABLE else "not available",
        "timestamp": datetime.now().isoformat()
    }
