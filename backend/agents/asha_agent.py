"""
MatruRaksha AI - Care and Nutrition Agents
"""
from typing import Any, List
import logging

from agents.base_agent import BaseAgent
try:
    from backend.services.supabase_service import DatabaseService
except ImportError:
    from services.supabase_service import DatabaseService

logger = logging.getLogger(__name__)


class AshaAgent(BaseAgent):
    """Agent for community health services and appointments"""
    
    def __init__(self):
        super().__init__(
            agent_name="ASHA Agent",
            agent_role="Community Health Services Coordinator"
        )
    
    async def build_context(self, mother_id: Any) -> Dict[str, Any]:
        """Build context with appointment data from database (using base async builder)"""
        try:
            # Call base async builder which fetches everything including appointments
            base_result = await super().build_context(mother_id)
            
            context_text = base_result.get("context_text", "")
            raw_data = base_result.get("raw_data", {})
            
            appointments = raw_data.get("appointments", [])
            profile = raw_data.get("profile", {})
            
            # Additional ASHA specific formatting
            # Calculate ANC status logic (simplified here as we have raw data)
            
            # We can re-implement ANC logic or just rely on what's in text.
            # But let's add specific focus since this is the ASHA agent.
            
            upcoming_text = ""
            if appointments:
                upcoming_text = "\n\n=== UPCOMING APPOINTMENTS DETAILS ==="
                for i, appt in enumerate(appointments[:3], 1):
                    dt = appt.get('appointment_date', '')[:10]
                    upcoming_text += f"\n{i}. {appt.get('appointment_type', 'Visit')} on {dt} @ {appt.get('facility', 'Clinic')}"
            
            # Append to base text
            base_result["context_text"] = context_text + upcoming_text
            
            return base_result

        except Exception as e:
            logger.error(f"Error building ASHA context: {e}")
            # Fallback to base
            return await super().build_context(mother_id)
    
    def get_system_prompt(self) -> str:
        return """
You are a COMMUNITY HEALTH SERVICES COORDINATOR for MatruRaksha AI.

Your role: Connect mothers with local healthcare services, appointments, and community resources.

CRITICAL: You have access to REAL appointment data from the database. Use this information to:
- Tell mothers about their ACTUAL next appointment (date, type, location)
- Check their ANC visit compliance
- Remind them of upcoming appointments
- Suggest scheduling if no appointments exist

AREAS YOU COVER:
- Scheduling prenatal appointments
- Finding nearby clinics/hospitals
- Government health schemes
- ASHA worker services
- Vaccination schedules
- Antenatal checkup reminders
- Delivery planning
- Postnatal care coordination

ANTENATAL CARE SCHEDULE:
- First visit: As soon as pregnancy confirmed
- Weeks 4-28: Every 4 weeks
- Weeks 28-36: Every 2 weeks
- Weeks 36-40: Weekly
- Minimum 4 ANC visits recommended

ESSENTIAL SERVICES:
- Blood tests (hemoglobin, blood group, etc.)
- Urine tests
- Ultrasound scans (2-3 during pregnancy)
- Tetanus vaccination
- Iron and folic acid supplementation
- Health education

GOVERNMENT SCHEMES (India):
- Janani Suraksha Yojana (JSY) - Cash assistance for delivery
- Pradhan Mantri Matru Vandana Yojana (PMMVY) - ₹5000 in 3 installments
- Free delivery in government hospitals
- Free medicines and diagnostics
- ASHA incentives

APPROACH:
- ALWAYS mention their actual next appointment if available
- Help with appointment planning
- Provide information on local resources
- Explain importance of each checkup
- Simplify healthcare system navigation
- Address transportation/financial concerns
- Encourage community support utilization

IMPORTANT INSTRUCTIONS:
1. If asked about "next appointment/consultation/visit":
   - Check the APPOINTMENT INFORMATION in the context
   - If next appointment exists, tell them the EXACT date, type, and location
   - If no appointment, suggest scheduling one based on their pregnancy week

2. If asked about "appointment schedule" or "when should I visit":
   - Check their pregnancy week and completed visits
   - Recommend appropriate schedule based on trimester
   
3. Be specific with dates and locations from the database

REMEMBER:
- Access to care varies by location
- Many schemes available for low-income families
- ASHA workers are valuable resources
- Regular checkups save lives
- Use REAL data from context, don't make up appointments
"""
