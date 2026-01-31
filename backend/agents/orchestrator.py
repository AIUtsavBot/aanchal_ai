"""
SantanRaksha AI - Orchestrator Agent
Routes messages to specialized agents based on intent classification

Maternal Health Agents (MatruRaksha):
- ASHA Agent: Community health, appointments, local resources
- Care Agent: General pregnancy care, wellness tips
- Emergency Agent: Urgent symptoms, crisis situations
- Medication Agent: Medicine queries, prescriptions, side effects
- Nutrition Agent: Diet plans, nutrition advice, recipes
- Risk Agent: Risk assessment, complications, warning signs

Postnatal & Child Health Agents (SantanRaksha):
- Postnatal Agent: Postnatal recovery, breastfeeding, mental health
- Pediatric Agent: Child illnesses, IMNCI protocols, general pediatric care
- Vaccine Agent: Vaccination schedule, reminders, side effects
- Growth Agent: Growth monitoring, WHO z-scores, feeding guidance
"""

import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import Gemini for intent classification
gemini_client = None
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception:
    GEMINI_AVAILABLE = False


class AgentType(Enum):
    """Available agent types"""
    # Maternal health agents
    ASHA = "asha_agent"
    CARE = "care_agent"
    EMERGENCY = "emergency_agent"
    MEDICATION = "medication_agent"
    NUTRITION = "nutrition_agent"
    RISK = "risk_agent"
    # Postnatal & child health agents (SantanRaksha)
    POSTNATAL = "postnatal_agent"
    PEDIATRIC = "pediatric_agent"
    VACCINE = "vaccine_agent"
    GROWTH = "growth_agent"
    GENERAL = "general"  # Fallback


class MessageIntent:
    """Message intent classification keywords"""
    EMERGENCY_KEYWORDS = [
        'bleeding', 'blood', 'pain', 'severe', 'emergency', 'help', 'urgent',
        'hospital', 'ambulance', 'cant breathe', "can't breathe", 'chest pain', 
        'dizzy', 'faint', 'contractions', 'baby not moving', 'fluid leaking',
        'heavy bleeding', 'unconscious', 'seizure', 'stroke'
    ]
    
    MEDICATION_KEYWORDS = [
        'medicine', 'medication', 'drug', 'pill', 'tablet', 'prescription',
        'dose', 'dosage', 'side effect', 'pharmacy', 'vitamin', 'supplement',
        'paracetamol', 'iron', 'folic acid', 'calcium', 'aspirin', 'antibiotic'
    ]
    
    NUTRITION_KEYWORDS = [
        'food', 'eat', 'diet', 'nutrition', 'meal', 'recipe', 'hungry',
        'weight', 'protein', 'calcium', 'vitamin', 'fruit', 'vegetable',
        'breakfast', 'lunch', 'dinner', 'snack', 'drink', 'water', 'healthy eating'
    ]
    
    RISK_KEYWORDS = [
        'risk', 'complication', 'danger', 'warning', 'concern', 'problem',
        'high blood pressure', 'diabetes', 'gestational', 'preeclampsia',
        'anemia', 'infection', 'fever', 'swelling', 'miscarriage'
    ]
    
    ASHA_KEYWORDS = [
        'appointment', 'visit', 'clinic', 'doctor', 'hospital', 'checkup',
        'anc', 'antenatal', 'vaccination', 'test', 'scan', 'ultrasound',
        'local', 'nearby', 'asha', 'health worker', 'community', 'nearest hospital'
    ]
    
    CARE_KEYWORDS = [
        'pregnancy', 'trimester', 'week', 'month', 'baby', 'fetus',
        'movement', 'kicks', 'development', 'normal', 'common',
        'symptom', 'feeling', 'tired', 'nausea', 'morning sickness', 'back pain'
    ]
    
    # SantanRaksha-specific keywords
    POSTNATAL_KEYWORDS = [
        'postnatal', 'postpartum', 'after delivery', 'after birth', 'recovery',
        'breastfeeding', 'breast feed', 'lactation', 'milk supply', 'cracked nipple',
        'cesarean', 'c-section', 'stitches', 'episiotomy', 'bleeding after delivery',
        'lochia', 'postpartum depression', 'baby blues', 'mood', 'sad', 'crying'
    ]
    
    PEDIATRIC_KEYWORDS = [
        'child', 'infant', 'newborn', 'toddler', 'kids', 'baby sick', 'baby fever',
        'cough', 'cold', 'diarrhea', 'vomiting', 'rash', 'ear infection', 'pneumonia',
        'baby not eating', 'baby crying', 'teething', 'sleep', 'baby development'
    ]
    
    VACCINE_KEYWORDS = [
        'vaccine', 'vaccination', 'immunization', 'bcg', 'opv', 'pentavalent',
        'measles', 'polio', 'dpt', 'vaccine due', 'vaccine schedule', 'booster',
        'vaccine side effect', 'vaccine safe', 'autism vaccine'
    ]
    
    GROWTH_KEYWORDS = [
        'growth', 'weight', 'height', 'underweight', 'malnutrition', 'stunted',
        'not gaining weight', 'feeding', 'food', 'solid food', 'complementary feeding',
        'diet', 'nutrition', 'meal plan', 'baby food', 'eating', 'growth chart'
    ]


class OrchestratorAgent:
    """
    Orchestrator that routes messages to appropriate specialized agents
    """
    
    def __init__(self):
        self.agents = {}
        self._load_agents()
    
    def _load_agents(self):
        """Lazy load agents when needed"""
        try:
            try:
                # Maternal health agents
                from backend.agents.asha_agent import AshaAgent
                from backend.agents.care_agent import CareAgent
                from backend.agents.emergency_agent import EmergencyAgent
                from backend.agents.medication_agent import MedicationAgent
                from backend.agents.nutrition_agent import NutritionAgent
                from backend.agents.risk_agent import RiskAgent
                # SantanRaksha agents
                from backend.agents.postnatal_agent import PostnatalAgent
                from backend.agents.pediatric_agent import PediatricAgent
                from backend.agents.vaccine_agent import VaccineAgent
                from backend.agents.growth_agent import GrowthAgent
            except ImportError:
                # Maternal health agents
                from agents.asha_agent import AshaAgent
                from agents.care_agent import CareAgent
                from agents.emergency_agent import EmergencyAgent
                from agents.medication_agent import MedicationAgent
                from agents.nutrition_agent import NutritionAgent
                from agents.risk_agent import RiskAgent
                # SantanRaksha agents
                from agents.postnatal_agent import PostnatalAgent
                from agents.pediatric_agent import PediatricAgent
                from agents.vaccine_agent import VaccineAgent
                from agents.growth_agent import GrowthAgent
            
            self.agents = {
                # Maternal health agents
                AgentType.ASHA: AshaAgent(),
                AgentType.CARE: CareAgent(),
                AgentType.EMERGENCY: EmergencyAgent(),
                AgentType.MEDICATION: MedicationAgent(),
                AgentType.NUTRITION: NutritionAgent(),
                AgentType.RISK: RiskAgent(),
                # SantanRaksha agents
                AgentType.POSTNATAL: PostnatalAgent(),
                AgentType.PEDIATRIC: PediatricAgent(),
                AgentType.VACCINE: VaccineAgent(),
                AgentType.GROWTH: GrowthAgent()
            }
            logger.info("✅ All agents loaded successfully")
        except ImportError as e:
            logger.warning(f"⚠️ Some agents not available: {e}")
            self.agents = {}
    
    def classify_intent(self, message: str, mother_context: Dict[str, Any] = None) -> AgentType:
        """
        Classify message intent using keyword matching + AI
        Returns the most appropriate agent type
        
        IMPORTANT: Checks delivery_status to route to correct system
        - pregnant → MatruRaksha agents (pregnancy care)
        - delivered/postnatal → SantanRaksha agents (postnatal + child)
        """
        message_lower = message.lower()
        
        # SYSTEM ROUTING: Check if mother has delivered
        is_postnatal = False
        if mother_context:
            delivery_status = mother_context.get('delivery_status', 'pregnant')
            active_system = mother_context.get('active_system', 'matruraksha')
            is_postnatal = (delivery_status in ['delivered', 'postnatal'] or active_system == 'santanraksha')
            
            if is_postnatal:
                logger.info(f"🍼 Mother has delivered - routing to SantanRaksha agents")
        
        # Priority 1: Emergency detection (highest priority for both systems)
        if any(keyword in message_lower for keyword in MessageIntent.EMERGENCY_KEYWORDS):
            logger.info(f"🚨 EMERGENCY detected: {message[:50]}")
            return AgentType.EMERGENCY
        
        # Priority 2: Specific domain keywords
        if is_postnatal:
            # POSTNATAL SYSTEM: Prioritize SantanRaksha agents
            keyword_scores = {
                AgentType.POSTNATAL: sum(1 for kw in MessageIntent.POSTNATAL_KEYWORDS if kw in message_lower),
                AgentType.PEDIATRIC: sum(1 for kw in MessageIntent.PEDIATRIC_KEYWORDS if kw in message_lower),
                AgentType.VACCINE: sum(1 for kw in MessageIntent.VACCINE_KEYWORDS if kw in message_lower),
                AgentType.GROWTH: sum(1 for kw in MessageIntent.GROWTH_KEYWORDS if kw in message_lower),
                # Emergency still available
                AgentType.EMERGENCY: 0
            }
        else:
            # PREGNANCY SYSTEM: Use MatruRaksha agents
            keyword_scores = {
                AgentType.MEDICATION: sum(1 for kw in MessageIntent.MEDICATION_KEYWORDS if kw in message_lower),
                AgentType.NUTRITION: sum(1 for kw in MessageIntent.NUTRITION_KEYWORDS if kw in message_lower),
                AgentType.RISK: sum(1 for kw in MessageIntent.RISK_KEYWORDS if kw in message_lower),
                AgentType.ASHA: sum(1 for kw in MessageIntent.ASHA_KEYWORDS if kw in message_lower),
                AgentType.CARE: sum(1 for kw in MessageIntent.CARE_KEYWORDS if kw in message_lower)
            }
        
        # Get highest scoring agent
        best_agent = max(keyword_scores.items(), key=lambda x: x[1])
        if best_agent[1] > 0:
            logger.info(f"📍 Intent classified: {best_agent[0].value} (score: {best_agent[1]}) [System: {'SantanRaksha' if is_postnatal else 'MatruRaksha'}]")
            return best_agent[0]
        
        # Priority 3: Use AI classification if available
        if GEMINI_AVAILABLE:
            try:
                ai_agent = self._ai_classify(message, is_postnatal)
                if ai_agent:
                    return ai_agent
            except Exception as e:
                logger.error(f"AI classification error: {e}")
        
        # Default based on system
        if is_postnatal:
            logger.info("📍 No specific intent - using POSTNATAL agent (SantanRaksha)")
            return AgentType.POSTNATAL
        else:
            logger.info("📍 No specific intent - using CARE agent (MatruRaksha)")
            return AgentType.CARE
    
    def _ai_classify(self, message: str, is_postnatal: bool = False) -> Optional[AgentType]:
        """Use Gemini AI for intent classification (fast)"""
        try:
            if not gemini_client:
                return None
            
            if is_postnatal:
                 prompt = f"""
Classify this postnatal/child health message into ONE category:
- EMERGENCY: urgent issues for mother or baby, severe pain, bleeding, difficulty breathing
- POSTNATAL: mother's recovery, breastfeeding, mental health, stitches, lochia
- PEDIATRIC: baby's health, sickness, fever, rash, crying, sleep
- VACCINE: immunizations, shots, schedule, side effects
- GROWTH: baby's weight, height, feeding, milestones

Message: "{message}"

Respond with ONLY the category name (one word).
"""
            else:
                prompt = f"""
Classify this maternal health message into ONE category:
- EMERGENCY: urgent medical issues, bleeding, severe pain, crisis
- MEDICATION: medicines, drugs, supplements, prescriptions
- NUTRITION: food, diet, meals, eating, recipes
- RISK: complications, risks, warning signs, concerns
- ASHA: appointments, clinics, local health services, checkups
- CARE: general pregnancy questions, symptoms, baby development

Message: "{message}"

Respond with ONLY the category name (one word).
"""
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            category = response.text.strip().upper()
            
            # Map to AgentType
            category_map = {
                'EMERGENCY': AgentType.EMERGENCY,
                'MEDICATION': AgentType.MEDICATION,
                'NUTRITION': AgentType.NUTRITION,
                'RISK': AgentType.RISK,
                'ASHA': AgentType.ASHA,
                'CARE': AgentType.CARE,
                # SantanRaksha mapping
                'POSTNATAL': AgentType.POSTNATAL,
                'PEDIATRIC': AgentType.PEDIATRIC,
                'VACCINE': AgentType.VACCINE,
                'GROWTH': AgentType.GROWTH
            }
            
            return category_map.get(category, AgentType.POSTNATAL if is_postnatal else AgentType.CARE)
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return None
    
    async def route_message(
        self, 
        message: str, 
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]]
    ) -> str:
        """
        Route message to appropriate agent and get response
        
        Args:
            message: User's message
            mother_context: Mother's profile data
            reports_context: Recent medical reports
            
        Returns:
            Agent's response text
        """
        # Classify intent (with mother context for system routing)
        agent_type = self.classify_intent(message, mother_context)
        
        # Get appropriate agent
        agent = self.agents.get(agent_type)
        
        if not agent:
            # Fallback to generic Gemini response if agent not available
            logger.warning(f"⚠️ Agent {agent_type} not available, using fallback")
            return await self._fallback_response(message, mother_context, reports_context)
        
        # Route to agent
        try:
            logger.info(f"📤 Routing to {agent_type.value}")
            lang = mother_context.get('preferred_language', 'en')
            response = await agent.process_query(
                query=message,
                mother_context=mother_context,
                reports_context=reports_context,
                language=lang
            )
            return response
        except Exception as e:
            logger.error(f"Agent {agent_type} error: {e}")
            return await self._fallback_response(message, mother_context, reports_context)
    
    async def _fallback_response(
        self, 
        message: str,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]]
    ) -> str:
        """Fallback response using Gemini directly"""
        if not GEMINI_AVAILABLE or not gemini_client:
            return (
                "⚠️ I'm sorry, I'm having trouble processing your request right now. "
                "Please try again in a moment or contact your healthcare provider if urgent."
            )
        
        try:
            model_name = (
                os.getenv('GEMINI_SFT_MODEL')
                or os.getenv('GEMINI_MODEL_NAME')
                or 'gemini-2.5-flash'
            )
            
            # Build context
            context_info = f"""
Mother Profile:
- Name: {mother_context.get('name')}
- Age: {mother_context.get('age')}
- Gravida: {mother_context.get('gravida')}
- Parity: {mother_context.get('parity')}
- BMI: {mother_context.get('bmi')}

Recent Reports: {len(reports_context)}
"""
            
            if reports_context:
                context_info += "\nRecent Analysis:\n"
                for i, report in enumerate(reports_context[:2], 1):
                    analysis = report.get('analysis_result', {})
                    if analysis:
                        risk = analysis.get('risk_level', 'unknown')
                        context_info += f"Report {i}: Risk Level - {risk}\n"
            
            prompt = f"""
You are a maternal health assistant for {mother_context.get('name')}.

{context_info}

User Question: {message}

Provide a helpful, empathetic response in 2-3 paragraphs.
If urgent, advise consulting healthcare provider immediately.

Response:
"""
            
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text.replace('*', '').replace('_', '').replace('`', '')
            
        except Exception as e:
            logger.error(f"Fallback response error: {e}")
            return (
                "I apologize, but I'm having difficulty processing your request. "
                "Please try rephrasing your question or contact your healthcare provider."
            )


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> OrchestratorAgent:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


async def route_message(
    message: str,
    mother_context: Dict[str, Any],
    reports_context: List[Dict[str, Any]],
) -> str:
    """
    Convenience wrapper so other modules can simply import `route_message`
    without managing orchestrator instances.
    """
    orchestrator = get_orchestrator()
    return await orchestrator.route_message(message, mother_context, reports_context)