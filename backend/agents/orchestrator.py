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
import time
import hashlib
from typing import Dict, Any, Optional, List
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)

# Try to import Gemini for intent classification
gemini_client = None
GEMINI_AVAILABLE = False
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
except Exception:
    pass


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
    """
    Multilingual intent classification keywords.
    Includes English, Hindi (Devanagari + transliteration), and Marathi.
    """

    EMERGENCY_KEYWORDS = {
        # (keyword, severity_weight): Higher weight = more urgent
        # English
        'bleeding': 8, 'blood': 5, 'hemorrhage': 10, 'haemorrhage': 10,
        'severe pain': 9, 'unbearable pain': 10, 'chest pain': 9,
        'cant breathe': 10, "can't breathe": 10, 'difficulty breathing': 9,
        'unconscious': 10, 'fainted': 8, 'seizure': 10, 'convulsion': 10,
        'baby not moving': 9, 'fluid leaking': 8, 'water broke': 8,
        'emergency': 10, 'urgent': 7, 'ambulance': 10, 'hospital': 4,
        'stroke': 10, 'contractions': 6, 'heavy bleeding': 10,
        'dizzy': 4, 'faint': 5, 'high fever': 7,
        'headache': 3, 'blurred vision': 7, 'swelling': 4,
        # Hindi (Devanagari)
        'खून': 7, 'रक्तस्राव': 9, 'दर्द': 5, 'तेज दर्द': 9,
        'बेहोश': 8, 'सांस': 6, 'मदद': 7, 'इमरजेंसी': 10,
        'अस्पताल': 4, 'एम्बुलेंस': 10, 'बुखार': 5, 'दौरा': 10,
        # Hindi (transliterated)
        'khoon': 7, 'dard': 5, 'behosh': 8, 'madad': 7,
        'ambulance': 10, 'bukhar': 5, 'daura': 10,
        # Marathi
        'रक्त': 7, 'वेदना': 5, 'बेशुद्ध': 8, 'श्वास': 6,
        'मदत': 7, 'इमर्जन्सी': 10, 'हॉस्पिटल': 4, 'ताप': 5,
    }

    MEDICATION_KEYWORDS = [
        # English
        'medicine', 'medication', 'drug', 'pill', 'tablet', 'prescription',
        'dose', 'dosage', 'side effect', 'pharmacy', 'vitamin', 'supplement',
        'paracetamol', 'iron', 'folic acid', 'calcium', 'aspirin', 'antibiotic',
        # Hindi
        'दवाई', 'दवा', 'गोली', 'औषधि', 'खुराक', 'विटामिन',
        'dawai', 'dawa', 'goli', 'vitamin',
        # Marathi
        'औषध', 'गोळी',
    ]

    NUTRITION_KEYWORDS = [
        # English
        'food', 'eat', 'diet', 'nutrition', 'meal', 'recipe', 'hungry',
        'weight gain', 'protein', 'fruit', 'vegetable',
        'breakfast', 'lunch', 'dinner', 'snack', 'drink', 'water', 'healthy eating',
        # Hindi
        'खाना', 'आहार', 'पोषण', 'भोजन', 'फल', 'सब्जी', 'दूध',
        'khana', 'aahar', 'poshan', 'bhojan', 'dudh',
        # Marathi
        'जेवण', 'आहार', 'पोषण', 'फळ', 'भाजी',
    ]

    RISK_KEYWORDS = [
        # English
        'risk', 'complication', 'danger', 'warning', 'concern', 'problem',
        'high blood pressure', 'diabetes', 'gestational', 'preeclampsia',
        'anemia', 'infection', 'miscarriage',
        # Hindi
        'खतरा', 'जटिलता', 'समस्या', 'चिंता', 'मधुमेह', 'रक्तचाप',
        'khatra', 'samasya', 'chinta',
        # Marathi
        'धोका', 'समस्या', 'चिंता',
    ]

    ASHA_KEYWORDS = [
        # English
        'appointment', 'visit', 'clinic', 'checkup',
        'anc', 'antenatal', 'test', 'scan', 'ultrasound',
        'local', 'nearby', 'asha', 'health worker', 'community', 'nearest hospital',
        # Hindi
        'मुलाकात', 'अस्पताल', 'जांच', 'आशा', 'दीदी',
        'mulakat', 'jaanch', 'asha didi',
        # Marathi
        'भेट', 'तपासणी', 'आशा', 'ताई',
    ]

    CARE_KEYWORDS = [
        # English
        'pregnancy', 'trimester', 'week', 'month', 'baby', 'fetus',
        'movement', 'kicks', 'development', 'normal', 'common',
        'symptom', 'feeling', 'tired', 'nausea', 'morning sickness', 'back pain',
        # Hindi
        'गर्भावस्था', 'माह', 'शिशु', 'बच्चा', 'हलचल', 'थकान', 'उल्टी',
        'garbhawastha', 'baccha', 'thakan', 'ulti',
        # Marathi
        'गर्भारपण', 'बाळ', 'हालचाल', 'थकवा', 'मळमळ',
    ]

    # SantanRaksha-specific keywords
    POSTNATAL_KEYWORDS = [
        # English
        'postnatal', 'postpartum', 'after delivery', 'after birth', 'recovery',
        'breastfeeding', 'breast feed', 'lactation', 'milk supply', 'cracked nipple',
        'cesarean', 'c-section', 'stitches', 'episiotomy', 'bleeding after delivery',
        'lochia', 'postpartum depression', 'baby blues', 'mood', 'sad', 'crying',
        # Hindi
        'प्रसव के बाद', 'स्तनपान', 'दूध', 'टांके', 'अवसाद',
        'stanpan', 'prasav ke baad',
        # Marathi
        'प्रसूतीनंतर', 'स्तनपान', 'टाके',
    ]

    PEDIATRIC_KEYWORDS = [
        # English
        'child', 'infant', 'newborn', 'toddler', 'kids', 'baby sick', 'baby fever',
        'cough', 'cold', 'diarrhea', 'vomiting', 'rash', 'ear infection', 'pneumonia',
        'baby not eating', 'baby crying', 'teething', 'sleep', 'baby development',
        # Hindi
        'बच्चा बीमार', 'खांसी', 'जुकाम', 'दस्त', 'उल्टी', 'दांत',
        'baccha bimar', 'khansi', 'jukaam', 'dast',
        # Marathi
        'बाळ आजारी', 'खोकला', 'सर्दी', 'जुलाब', 'उलटी', 'दात',
    ]

    VACCINE_KEYWORDS = [
        # English
        'vaccine', 'vaccination', 'immunization', 'bcg', 'opv', 'pentavalent',
        'measles', 'polio', 'dpt', 'vaccine due', 'vaccine schedule', 'booster',
        'vaccine side effect', 'vaccine safe',
        # Hindi
        'टीका', 'टीकाकरण', 'वैक्सीन',
        'teeka', 'teekakaran', 'vaccine',
        # Marathi
        'लस', 'लसीकरण',
    ]

    GROWTH_KEYWORDS = [
        # English
        'growth', 'weight', 'height', 'underweight', 'malnutrition', 'stunted',
        'not gaining weight', 'feeding', 'solid food', 'complementary feeding',
        'meal plan', 'baby food', 'growth chart',
        # Hindi
        'वजन', 'ऊंचाई', 'कुपोषण', 'खिलाना', 'आहार',
        'vajan', 'kuposhan', 'khilana',
        # Marathi
        'वजन', 'उंची', 'कुपोषण',
    ]


# ==================== CLASSIFICATION CACHE ====================
# LRU cache to avoid repeated Gemini API calls for identical/similar messages
_classification_cache: Dict[str, tuple] = {}  # hash -> (agent_type, timestamp)
CACHE_TTL = 300  # 5 minutes

def _get_cache_key(message: str, is_postnatal: bool) -> str:
    """Generate cache key from normalized message + system context."""
    normalized = message.lower().strip()[:200]  # Limit to first 200 chars for cache
    return hashlib.md5(f"{normalized}:{is_postnatal}".encode()).hexdigest()

def _get_cached_classification(message: str, is_postnatal: bool) -> Optional[AgentType]:
    """Check cache for previous classification result."""
    key = _get_cache_key(message, is_postnatal)
    if key in _classification_cache:
        agent_type, ts = _classification_cache[key]
        if time.time() - ts < CACHE_TTL:
            logger.debug(f"🎯 Cache hit for classification: {agent_type.value}")
            return agent_type
        del _classification_cache[key]
    return None

def _cache_classification(message: str, is_postnatal: bool, agent_type: AgentType):
    """Store classification result in cache."""
    key = _get_cache_key(message, is_postnatal)
    _classification_cache[key] = (agent_type, time.time())
    # Evict old entries if cache grows too large
    if len(_classification_cache) > 500:
        cutoff = time.time() - CACHE_TTL
        expired = [k for k, (_, ts) in _classification_cache.items() if ts < cutoff]
        for k in expired:
            del _classification_cache[k]


class OrchestratorAgent:
    """
    Orchestrator that routes messages to appropriate specialized agents.
    Uses keyword scoring + AI fallback with caching to minimize API calls.
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
        Classify message intent using:
        1. Severity-weighted emergency detection
        2. Multilingual keyword scoring with overlap resolution
        3. Cached AI classification (only if keywords are ambiguous)
        4. System routing based on delivery_status

        Returns the most appropriate agent type.
        """
        message_lower = message.lower()

        # SYSTEM ROUTING: Check if mother has delivered
        is_postnatal = False
        if mother_context:
            delivery_status = mother_context.get('delivery_status', 'pregnant')
            active_system = mother_context.get('active_system', 'matruraksha')
            is_postnatal = (delivery_status in ['delivered', 'postnatal'] or active_system == 'santanraksha')

            if is_postnatal:
                logger.info("🍼 Mother has delivered — routing to SantanRaksha agents")

        # Check cache first (avoids redundant AI calls)
        cached = _get_cached_classification(message, is_postnatal)
        if cached:
            return cached

        # Priority 1: Severity-weighted emergency detection
        emergency_score = 0
        matched_emergency = []
        for keyword, weight in MessageIntent.EMERGENCY_KEYWORDS.items():
            if keyword in message_lower:
                emergency_score += weight
                matched_emergency.append(keyword)

        # Threshold: score >= 7 qualifies as emergency
        # This prevents low-severity matches like "hospital" alone from triggering
        if emergency_score >= 7:
            logger.info(f"🚨 EMERGENCY detected (score={emergency_score}): {matched_emergency}")
            _cache_classification(message, is_postnatal, AgentType.EMERGENCY)
            return AgentType.EMERGENCY

        # Priority 2: Multilingual keyword scoring
        if is_postnatal:
            keyword_scores = {
                AgentType.POSTNATAL: sum(1 for kw in MessageIntent.POSTNATAL_KEYWORDS if kw in message_lower),
                AgentType.PEDIATRIC: sum(1 for kw in MessageIntent.PEDIATRIC_KEYWORDS if kw in message_lower),
                AgentType.VACCINE: sum(1 for kw in MessageIntent.VACCINE_KEYWORDS if kw in message_lower),
                AgentType.GROWTH: sum(1 for kw in MessageIntent.GROWTH_KEYWORDS if kw in message_lower),
            }
        else:
            keyword_scores = {
                AgentType.MEDICATION: sum(1 for kw in MessageIntent.MEDICATION_KEYWORDS if kw in message_lower),
                AgentType.NUTRITION: sum(1 for kw in MessageIntent.NUTRITION_KEYWORDS if kw in message_lower),
                AgentType.RISK: sum(1 for kw in MessageIntent.RISK_KEYWORDS if kw in message_lower),
                AgentType.ASHA: sum(1 for kw in MessageIntent.ASHA_KEYWORDS if kw in message_lower),
                AgentType.CARE: sum(1 for kw in MessageIntent.CARE_KEYWORDS if kw in message_lower),
            }

        # Remove overlapping keywords — require score >= 2 for confident routing
        # If only one keyword matched, or top two agents are tied, use AI
        sorted_agents = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        best_agent, best_score = sorted_agents[0]
        second_score = sorted_agents[1][1] if len(sorted_agents) > 1 else 0

        if best_score >= 2 and best_score > second_score:
            # Confident keyword match
            logger.info(f"📍 Intent: {best_agent.value} (score={best_score}, clear winner) [{'SantanRaksha' if is_postnatal else 'MatruRaksha'}]")
            _cache_classification(message, is_postnatal, best_agent)
            return best_agent

        if best_score == 1 and second_score == 0:
            # Single weak match — still use it but log uncertainty
            logger.info(f"📍 Intent: {best_agent.value} (score=1, weak) [{'SantanRaksha' if is_postnatal else 'MatruRaksha'}]")
            _cache_classification(message, is_postnatal, best_agent)
            return best_agent

        # Priority 3: AI classification for ambiguous/no-match messages
        if GEMINI_AVAILABLE:
            try:
                ai_agent = self._ai_classify(message, is_postnatal)
                if ai_agent:
                    _cache_classification(message, is_postnatal, ai_agent)
                    return ai_agent
            except Exception as e:
                logger.error(f"AI classification error: {e}")

        # Default based on system
        default = AgentType.POSTNATAL if is_postnatal else AgentType.CARE
        logger.info(f"📍 No clear intent — defaulting to {default.value}")
        _cache_classification(message, is_postnatal, default)
        return default

    def _ai_classify(self, message: str, is_postnatal: bool = False) -> Optional[AgentType]:
        """
        Use Gemini AI for intent classification.
        Optimized prompt to minimize token usage (~100 input tokens).
        """
        try:
            if not gemini_client:
                return None

            # Compact prompt to save tokens
            if is_postnatal:
                prompt = (
                    "Classify into ONE: EMERGENCY/POSTNATAL/PEDIATRIC/VACCINE/GROWTH\n"
                    f"Message: \"{message[:300]}\"\n"
                    "Reply with ONE word only."
                )
            else:
                prompt = (
                    "Classify into ONE: EMERGENCY/MEDICATION/NUTRITION/RISK/ASHA/CARE\n"
                    f"Message: \"{message[:300]}\"\n"
                    "Reply with ONE word only."
                )

            response = gemini_client.models.generate_content(
                model='gemini-2.0-flash',  # Cheaper, faster model for classification
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
                'POSTNATAL': AgentType.POSTNATAL,
                'PEDIATRIC': AgentType.PEDIATRIC,
                'VACCINE': AgentType.VACCINE,
                'GROWTH': AgentType.GROWTH,
            }

            result = category_map.get(category)
            if result:
                logger.info(f"🤖 AI classified: {result.value}")
                return result

            return AgentType.POSTNATAL if is_postnatal else AgentType.CARE

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
        Route message to appropriate agent and get response.

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
        """Fallback response using Gemini directly — optimized prompt for fewer tokens."""
        if not GEMINI_AVAILABLE or not gemini_client:
            return (
                "⚠️ I'm sorry, I'm having trouble processing your request right now. "
                "Please try again in a moment or contact your healthcare provider if urgent."
            )

        try:
            model_name = (
                os.getenv('GEMINI_SFT_MODEL')
                or os.getenv('GEMINI_MODEL_NAME')
                or 'gemini-2.0-flash'
            )

            # Compact context — only include non-null fields to save tokens
            context_parts = []
            name = mother_context.get('name')
            if name:
                context_parts.append(f"Name: {name}")
            age = mother_context.get('age')
            if age:
                context_parts.append(f"Age: {age}")
            gravida = mother_context.get('gravida')
            if gravida:
                context_parts.append(f"G{gravida}P{mother_context.get('parity', '?')}")
            bmi = mother_context.get('bmi')
            if bmi:
                context_parts.append(f"BMI: {bmi}")

            context_str = ", ".join(context_parts) if context_parts else "Unknown"

            # Include conversation memory if available
            memory_hint = ""
            follow_up = mother_context.get('follow_up_prompt', '')
            if follow_up:
                memory_hint = f"\nConversation context: {follow_up[:300]}"

            prompt = (
                f"You are a maternal health assistant for: {context_str}.{memory_hint}\n\n"
                f"Question: {message}\n\n"
                "Reply empathetically in 2-3 short paragraphs. "
                "Ask 2-3 clarifying questions before advising. "
                "If urgent, advise consulting healthcare provider."
            )

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