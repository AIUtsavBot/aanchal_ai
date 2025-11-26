"""
MatruRaksha AI - Base Agent Class
All specialized agents inherit from this base class
"""

import os
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except:
    GEMINI_AVAILABLE = False

# Select model via env hook (supports fine-tuned model names)
GEMINI_MODEL_NAME = (
    os.getenv("GEMINI_SFT_MODEL")
    or os.getenv("GEMINI_MODEL_NAME")
    or "gemini-2.5-flash"
)


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_name: str, agent_role: str):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.model = None
        
        if GEMINI_AVAILABLE:
            try:
                self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
                logger.info(f"✅ {agent_name} initialized with Gemini model: {GEMINI_MODEL_NAME}")
            except Exception as e:
                logger.error(f"❌ {agent_name} failed to initialize: {e}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    def build_context(self, mother_id: Any) -> str:
        try:
            from backend.services.supabase_service import DatabaseService
            from backend.utils.toon_helper import json_to_toon
        except ImportError:
            from services.supabase_service import DatabaseService
            from utils.toon_helper import json_to_toon
        data = DatabaseService.get_mother_holistic_data(mother_id)
        profile = data.get('profile') or {}
        context_parts = [
            "===== COMPREHENSIVE MOTHER PROFILE =====",
            f"Name: {profile.get('name', 'N/A')}",
            f"Age: {profile.get('age', 'N/A')} years",
            f"Gravida: {profile.get('gravida', 'N/A')}",
            f"Parity: {profile.get('parity', 'N/A')}",
            f"BMI: {profile.get('bmi', 'N/A')}",
            f"Location: {profile.get('location', 'N/A')}",
        ]
        
        # Add due date if available
        due_date = profile.get('due_date')
        if due_date:
            try:
                from datetime import datetime
                due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                due_str = due_dt.strftime("%B %d, %Y")
                # Calculate pregnancy week (assuming 40 weeks from LMP to due date)
                today = datetime.now()
                if due_dt > today:
                    # Due date is in the future - calculate weeks remaining
                    days_remaining = (due_dt - today).days
                    weeks_remaining = days_remaining // 7
                    weeks_pregnant = 40 - weeks_remaining
                    if weeks_pregnant < 0:
                        weeks_pregnant = 0
                    if weeks_pregnant > 40:
                        weeks_pregnant = 40
                    months_pregnant = (weeks_pregnant // 4) + 1
                    trimester = "First" if weeks_pregnant <= 13 else ("Second" if weeks_pregnant <= 27 else "Third")
                    context_parts.append(f"Due Date: {due_str}")
                    context_parts.append(f"Current Pregnancy: {weeks_pregnant} weeks ({months_pregnant} months) - {trimester} Trimester")
                else:
                    context_parts.append(f"Due Date: {due_str} (Past due date)")
            except:
                context_parts.append(f"Due Date: {due_date[:10] if due_date else 'Not set'}")
        
        context_parts.append("")
        
        # Add appointments if available
        next_appt = None
        appointments = []
        
        if next_appt:
            appt_date = next_appt.get('appointment_date', '')
            appt_type = next_appt.get('appointment_type', '')
            facility = next_appt.get('facility', '')
            status = next_appt.get('status', '')
            try:
                from datetime import datetime
                appt_dt = datetime.fromisoformat(appt_date.replace('Z', '+00:00'))
                pretty_date = appt_dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pretty_date = appt_date
            context_parts.append("===== NEXT APPOINTMENT =====")
            context_parts.append(f"Date/Time: {pretty_date}")
            if facility:
                context_parts.append(f"Facility: {facility}")
            if appt_type:
                context_parts.append(f"Type: {appt_type}")
            if status:
                context_parts.append(f"Status: {status}")
            context_parts.append("")
        elif appointments:
            # If no next_appointment but appointments list exists, use first one
            appt = appointments[0]
            appt_date = appt.get('appointment_date', '')
            facility = appt.get('facility', '')
            appt_type = appt.get('appointment_type', '')
            try:
                from datetime import datetime
                appt_dt = datetime.fromisoformat(appt_date.replace('Z', '+00:00'))
                pretty_date = appt_dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pretty_date = appt_date
            context_parts.append("===== UPCOMING APPOINTMENT =====")
            context_parts.append(f"Date/Time: {pretty_date}")
            if facility:
                context_parts.append(f"Facility: {facility}")
            if appt_type:
                context_parts.append(f"Type: {appt_type}")
            context_parts.append("")
        
        # Add health timeline/vitals if available
        timeline = []
        if timeline:
            context_parts.append("===== RECENT HEALTH EVENTS & VITALS =====")
            recent_vitals = {}
            for event in timeline[:10]:  # Last 10 events
                event_type = event.get('event_type', '')
                event_date = event.get('event_date') or event.get('date', '')[:10]
                if event_type.lower() in ['vitals', 'checkup', 'lab']:
                    vitals_data = event.get('event_data') or event.get('data', {})
                    if isinstance(vitals_data, str):
                        try:
                            import json
                            vitals_data = json.loads(vitals_data)
                        except:
                            vitals_data = {}
                    if vitals_data:
                        for key, value in vitals_data.items():
                            if key.lower() in ['bp', 'blood_pressure', 'hb', 'hemoglobin', 'sugar', 'glucose', 'weight']:
                                recent_vitals[key] = value
            if recent_vitals:
                for key, value in recent_vitals.items():
                    context_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            context_parts.append("")
        
        
        
        # Add context memories (TOON summaries, concerns, facts)
        memories = []
        if memories:
            context_parts.append("===== KEY HEALTH MEMORIES & CONCERNS =====")
            for mem in memories[:10]:  # Last 10 memories
                mem_key = mem.get('memory_key', '')
                mem_value = mem.get('memory_value', '')
                mem_type = mem.get('memory_type', '')
                if mem_value:
                    if mem_type == 'concern':
                        context_parts.append(f"⚠️ Concern: {mem_value}")
                    elif 'toon' in mem_key.lower():
                        context_parts.append(f"📋 Summary: {mem_value}")
                    else:
                        context_parts.append(f"💡 {mem_key}: {mem_value}")
            context_parts.append("")
        
        # Add any additional health metrics from context
        hist = data.get('medical_history') or {}
        toon = json_to_toon(hist)
        if toon:
            context_parts.append("===== TOON MEDICAL HISTORY =====")
            context_parts.append(toon)
            context_parts.append("")
        risks = data.get('risk_assessments') or []
        metrics = data.get('recent_metrics') or []
        if risks or metrics:
            context_parts.append("===== RECENT VITALS =====")
            for r in risks[:3]:
                bp = None
                if r.get('systolic_bp') and r.get('diastolic_bp'):
                    bp = f"{r.get('systolic_bp')}/{r.get('diastolic_bp')}"
                if bp:
                    context_parts.append(f"Blood Pressure: {bp}")
                if r.get('hemoglobin') is not None:
                    context_parts.append(f"Hemoglobin: {r.get('hemoglobin')}")
                if r.get('blood_glucose') is not None:
                    context_parts.append(f"Blood Glucose: {r.get('blood_glucose')}")
                if r.get('heart_rate') is not None:
                    context_parts.append(f"Heart Rate: {r.get('heart_rate')}")
            for m in metrics[:3]:
                if m.get('blood_pressure_systolic') and m.get('blood_pressure_diastolic'):
                    context_parts.append(f"Blood Pressure: {m.get('blood_pressure_systolic')}/{m.get('blood_pressure_diastolic')}")
                if m.get('hemoglobin') is not None:
                    context_parts.append(f"Hemoglobin: {m.get('hemoglobin')}")
                if m.get('blood_sugar') is not None:
                    context_parts.append(f"Blood Sugar: {m.get('blood_sugar')}")
                if m.get('weight_kg') is not None:
                    context_parts.append(f"Weight: {m.get('weight_kg')}")
            context_parts.append("")
        asha = data.get('asha_worker')
        if asha:
            context_parts.append("===== ASSIGNED ASHA WORKER =====")
            context_parts.append(f"Name: {asha.get('name')}")
            if asha.get('phone'):
                context_parts.append(f"Phone: {asha.get('phone')}")
            if asha.get('assigned_area'):
                context_parts.append(f"Area: {asha.get('assigned_area')}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def process_query(
        self,
        query: str,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]],
        language: str = 'en'
    ) -> str:
        """Process a query and return response"""
        if not self.model:
            return (
                f"⚠️ {self.agent_name} is currently unavailable. "
                "Please try again later or contact support."
            )
        
        try:
            # Build full prompt
            system_prompt = self.get_system_prompt()
            context_info = self.build_context(mother_context.get('id'))
            preferred_language = language or mother_context.get('preferred_language', 'en')
            
            full_prompt = f"""
CRITICAL: Strictly follow WHO and NHM India guidelines. If High Risk, recommend hospital. Reply ONLY in {preferred_language}.

{system_prompt}

{context_info}

User Question: {query}

Response:
"""
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Clean response
            cleaned_response = response.text.strip()
            
            logger.info(f"✅ {self.agent_name} processed query successfully")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} error: {e}")
            return (
                f"I apologize, but I encountered an issue processing your request. "
                f"Please try rephrasing your question or contact your healthcare provider if urgent."
            )
