"""
MatruRaksha AI - Memory & Context Service with Gemini
File: services/memory_service.py
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import google.generativeai as genai
from supabase import create_client

logger = logging.getLogger(__name__)

# Initialize clients
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


class GeminiService:
    """
    Service for AI responses using Google Gemini
    Manages mother-specific AI agents with memory
    """
    
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.warning("⚠️  GEMINI_API_KEY not set")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini service initialized")
        self.db = supabase
    
    async def get_or_create_agent(
        self,
        mother_id: str,
        mother_name: str,
        mother_profile: Dict
    ) -> str:
        """
        Create agent configuration for mother
        """
        
        if not self.db:
            return None
        
        # Check if exists
        result = self.db.table("agent_configs")\
            .select("agent_id")\
            .eq("mother_id", mother_id)\
            .execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"✅ Found existing agent for mother {mother_id}")
            return result.data[0]["agent_id"]
        
        # Create personalized system prompt
        system_prompt = f"""You are MatruRaksha AI, a caring maternal health assistant for {mother_name}.

Your role:
- Analyze medical reports and provide clear health insights
- Answer questions using {mother_name}'s complete medical history
- Provide personalized, evidence-based health advice
- Be warm, empathetic, and encouraging
- Always prioritize her safety and wellbeing

Mother's profile:
- Name: {mother_name}
- Age: {mother_profile.get('age', 'N/A')} years
- Location: {mother_profile.get('location', 'N/A')}
- Preferred Language: {mother_profile.get('language', 'English')}
- BMI: {mother_profile.get('bmi', 'N/A')}

Guidelines:
- Use her medical history to give personalized advice
- Refer to previous reports and measurements
- Explain medical terms in simple language
- Be supportive and positive
- Alert about concerning symptoms immediately
"""
        
        # Store config
        try:
            self.db.table("agent_configs").insert({
                "mother_id": mother_id,
                "datastore_id": f"gemini_mother_{mother_id}",
                "agent_id": f"agent_{mother_id}",
                "system_prompt": system_prompt,
                "active": True,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            logger.info(f"✅ Created new agent config for mother {mother_id}")
            return f"agent_{mother_id}"
            
        except Exception as e:
            logger.error(f"Error creating agent config: {e}")
            return None
    
    async def query_agent(
        self,
        mother_id: str,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Query using Gemini with mother's full context
        """
        
        if not self.model:
            return "AI service is not available. Please set GEMINI_API_KEY in configuration."
        
        try:
            # Get personalized system prompt
            system_prompt = "You are MatruRaksha AI, a helpful maternal health assistant."
            
            if self.db:
                config = self.db.table("agent_configs")\
                    .select("system_prompt")\
                    .eq("mother_id", mother_id)\
                    .execute()
                
                if config.data and len(config.data) > 0:
                    system_prompt = config.data[0]["system_prompt"]
            
            # Build comprehensive prompt with context
            full_prompt = f"""{system_prompt}

"""
            
            # Add context from memory if provided
            if context:
                full_prompt += f"""===== MEDICAL HISTORY & CONTEXT =====
{context}

"""
            
            # Add user query
            full_prompt += f"""===== USER QUESTION =====
{query}

===== YOUR RESPONSE =====
Provide a helpful, personalized answer based on the context above. Be warm, clear, and supportive."""
            
            # Call Gemini
            response = self.model.generate_content(full_prompt)
            answer = response.text
            
            logger.info(f"✅ Generated response for mother {mother_id}")
            return answer
            
        except Exception as e:
            logger.error(f"Error querying Gemini: {e}", exc_info=True)
            return "I'm having trouble processing your question right now. Please try again in a moment."


class MemoryService:
    """Service for managing mother's health context and memory"""
    
    def __init__(self):
        self.db = supabase
    
    async def store_memory(
        self,
        mother_id: str,
        key: str,
        value: str,
        memory_type: str = "fact",
        source: str = "system"
    ):
        """Store a memory/context for mother"""
        
        if not self.db:
            logger.warning("⚠️  Database not available - cannot store memory")
            return
        
        try:
            self.db.table("context_memory").insert({
                "mother_id": int(mother_id) if str(mother_id).isdigit() else mother_id,
                "memory_key": key,
                "memory_value": value,
                "memory_type": memory_type,
                "source": source,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            logger.info(f"✅ Stored memory: {key} for mother {mother_id}")
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
    
    async def get_relevant_memories(
        self,
        mother_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """Get relevant memories for mother"""
        
        if not self.db:
            return []
        
        try:
            result = self.db.table("context_memory")\
                .select("*")\
                .eq("mother_id", int(mother_id) if str(mother_id).isdigit() else mother_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []
    
    async def build_context_string(
        self,
        mother_id: str,
        include_timeline: bool = True,
        include_reports: bool = True
    ) -> str:
        """Build comprehensive context string for AI queries"""
        
        context_parts = []
        
        # 1. Get stored memories
        memories = await self.get_relevant_memories(mother_id, limit=15)
        if memories:
            memory_text = "📝 Previous Health Context:\n"
            for mem in memories[:10]:
                key = mem.get('memory_key', 'Unknown')
                value = mem.get('memory_value', '')
                memory_text += f"• {key}: {value}\n"
            context_parts.append(memory_text)
        
        # 2. Get recent health timeline
        if include_timeline and self.db:
            try:
                timeline = self.db.table("health_timeline")\
                    .select("*")\
                    .eq("mother_id", int(mother_id) if str(mother_id).isdigit() else mother_id)\
                    .order("event_date", desc=True)\
                    .limit(5)\
                    .execute()
                
                if timeline.data:
                    timeline_text = "\n📅 Recent Health Timeline:\n"
                    for event in timeline.data:
                        date = event.get('event_date', 'Unknown date')
                        summary = event.get('summary', 'Health update')
                        bp = event.get('blood_pressure', '')
                        hb = event.get('hemoglobin', '')
                        
                        timeline_text += f"• {date}: {summary}"
                        if bp:
                            timeline_text += f" (BP: {bp})"
                        if hb:
                            timeline_text += f" (Hb: {hb})"
                        timeline_text += "\n"
                    
                    context_parts.append(timeline_text)
            except Exception as e:
                logger.error(f"Error getting timeline: {e}")
        
        # 3. Get recent medical reports
        if include_reports and self.db:
            try:
                reports = self.db.table("medical_reports")\
                    .select("filename, analysis_summary, upload_date, health_metrics")\
                    .eq("mother_id", int(mother_id) if str(mother_id).isdigit() else mother_id)\
                    .order("upload_date", desc=True)\
                    .limit(3)\
                    .execute()
                
                if reports.data:
                    reports_text = "\n📄 Recent Medical Reports:\n"
                    for report in reports.data:
                        filename = report.get('filename', 'Unknown')
                        summary = report.get('analysis_summary', 'No summary')
                        date = report.get('upload_date', '')[:10] if report.get('upload_date') else 'Unknown date'
                        
                        reports_text += f"• {date} - {filename}:\n"
                        reports_text += f"  {summary}\n"
                        
                        # Add key metrics if available
                        metrics = report.get('health_metrics')
                        if metrics:
                            try:
                                if isinstance(metrics, str):
                                    metrics = json.loads(metrics)
                                if metrics:
                                    reports_text += "  Metrics: "
                                    for key, value in metrics.items():
                                        if value:
                                            reports_text += f"{key}={value}, "
                                    reports_text += "\n"
                            except:
                                pass
                    
                    context_parts.append(reports_text)
            except Exception as e:
                logger.error(f"Error getting reports: {e}")
        
        if context_parts:
            return "\n".join(context_parts)
        else:
            return "No previous medical history available yet."
    
    async def store_document_analysis(
        self,
        mother_id: str,
        filename: str,
        analysis: Dict,
        document_id: Optional[str] = None
    ):
        """Store analyzed document information in database and memory"""
        
        if not self.db:
            logger.warning("⚠️  Database not available")
            return
        
        try:
            # Store in medical_reports table
            self.db.table("medical_reports").insert({
                "mother_id": int(mother_id) if str(mother_id).isdigit() else mother_id,
                "filename": filename,
                "analysis_summary": analysis.get("analysis_summary", ""),
                "health_metrics": json.dumps(analysis.get("health_metrics", {})),
                "concerns": json.dumps(analysis.get("concerns", [])),
                "recommendations": json.dumps(analysis.get("recommendations", [])),
                "document_id": document_id,
                "processed": True,
                "upload_date": datetime.now().isoformat()
            }).execute()
            
            logger.info(f"✅ Stored document analysis in database")
            
            # Store key metrics as memories for easy retrieval
            metrics = analysis.get("health_metrics", {})
            if metrics:
                for key, value in metrics.items():
                    if value and value != "null" and str(value).lower() != "none":
                        await self.store_memory(
                            mother_id,
                            f"latest_{key}",
                            str(value),
                            "health_metric",
                            "document"
                        )
            
            # Store concerns as memories
            concerns = analysis.get("concerns", [])
            if concerns:
                concerns_text = "; ".join(concerns[:3])
                await self.store_memory(
                    mother_id,
                    f"recent_concerns_{datetime.now().strftime('%Y%m%d')}",
                    concerns_text,
                    "concern",
                    "document"
                )
            
            logger.info(f"✅ Stored document context in memory")
            
        except Exception as e:
            logger.error(f"Error storing document analysis: {e}", exc_info=True)


# Global instances
gemini_service = GeminiService() if GEMINI_API_KEY else None
memory_service = MemoryService() if supabase else None

# For backwards compatibility
contextual_service = gemini_service


from typing import Any, Dict
from supabase import Client
from .supabase_service import SupabaseService


def build_context_string(mother_id: int, supabase: Client) -> str:
    svc = SupabaseService(supabase)

    profile = svc.get_mother_profile(mother_id)
    reports = svc.get_medical_reports(mother_id, limit=3)

    # Health timeline alignment: order by `event_date`
    tl_resp = supabase.table("health_timeline").select("*") \
        .eq("mother_id", mother_id).order("event_date", desc=True).limit(10).execute()
    timeline = tl_resp.data or []

    next_appt = svc.get_next_appointment(mother_id)

    lines = []
    lines.append(f"Mother ID: {mother_id}")
    if profile:
        lines.append(f"Age: {profile.get('age')} | Gravida: {profile.get('gravida')} | Location: {profile.get('location')}")

    # Extract recent vitals from timeline (blood_pressure, hemoglobin, sugar_level, weight)
    recent_bp = None
    recent_hb = None
    recent_sugar = None
    recent_weight = profile.get("weight_kg") if profile else None
    for e in timeline:
        try:
            bp_str = e.get("blood_pressure")
            if bp_str and not recent_bp:
                recent_bp = str(bp_str)
        except Exception:
            pass
        if not recent_hb and e.get("hemoglobin") is not None:
            recent_hb = e.get("hemoglobin")
        if e.get("weight") is not None:
            recent_weight = e.get("weight")
        if not recent_sugar:
            bs = e.get("blood_sugar")
            sl = e.get("sugar_level")
            if bs is not None:
                recent_sugar = bs
            elif sl is not None:
                recent_sugar = sl

    lines.append(f"Recent BP: {recent_bp} | Hb: {recent_hb} | Sugar: {recent_sugar}")
    lines.append(f"Weight(kg): {recent_weight}")

    # Appointment details
    if next_appt:
        appt_date = next_appt.get("appointment_date")
        appt_type = next_appt.get("appointment_type") or next_appt.get("purpose")
        facility = next_appt.get("facility")
        status = next_appt.get("status")
        lines.append("Next Appointment:")
        lines.append(f"- Date: {appt_date}")
        if facility:
            lines.append(f"- Facility: {facility}")
        if appt_type:
            lines.append(f"- Type: {appt_type}")
        if status:
            lines.append(f"- Status: {status}")

    if reports:
        lines.append("Recent Report Summaries:")
        for r in reports:
            lines.append(f"- {r.get('analysis_summary', '')}")

    return "\n".join(lines)


async def save_chat_history(
    mother_id: Optional[str],
    message_type: str,
    message_content: str,
    telegram_chat_id: Optional[str] = None,
    status: str = "success",
) -> bool:
    """
    Persist chat exchanges into `telegram_logs` so conversations can be reviewed later.
    """
    if not supabase:
        logger.warning("⚠️  Supabase client not available; skipping chat log write")
        return False

    payload = {
        "mother_id": str(mother_id) if mother_id else None,
        "chat_id": str(telegram_chat_id) if telegram_chat_id else None,
        "message_type": message_type,
        "message_content": message_content,
        "status": status,
        "created_at": datetime.now().isoformat(),
    }

    # Drop None values to avoid Supabase errors
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        supabase.table("telegram_logs").insert(payload).execute()
        logger.debug("💬 Chat history saved to telegram_logs")
        return True
    except Exception as exc:
        logger.error(f"❌ Failed to save chat history: {exc}", exc_info=True)
        return False
