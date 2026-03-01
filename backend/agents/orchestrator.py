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
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from functools import lru_cache
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Explicitly load .env from the backend directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Use shared Gemini key rotator (auto-rotates on 429)
try:
    from services.gemini_rotator import gemini_rotator
    gemini_client = gemini_rotator
    GEMINI_AVAILABLE = gemini_rotator.is_available
    logger.info(f"✅ Orchestrator using GeminiKeyRotator ({len(gemini_rotator._keys)} key(s))")
except ImportError:
    try:
        from backend.services.gemini_rotator import gemini_rotator
        gemini_client = gemini_rotator
        GEMINI_AVAILABLE = gemini_rotator.is_available
    except ImportError:
        gemini_client = None
        GEMINI_AVAILABLE = False

# Try to import Groq for intent classification/fallback
groq_client = None
GROQ_AVAILABLE = False
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_groq_api_key_here":
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
        logger.info(f"✅ Orchestrator using Groq key: ...{GROQ_API_KEY[-6:]}")
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

        # Priority 2: AI Zero-Shot Classification (Native language handling)
        if GROQ_AVAILABLE or GEMINI_AVAILABLE:
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
        Use Groq (or fallback to Gemini) AI for intent classification.
        Optimized prompt to minimize token usage (~100 input tokens).
        """
        try:
            if not groq_client and not gemini_client:
                return None

            # Compact prompt to save tokens
            if is_postnatal:
                prompt = (
                    "Classify into ONE of these words: EMERGENCY, POSTNATAL, PEDIATRIC, VACCINE, GROWTH\n"
                    f"Message: \"{message[:300]}\"\n"
                    "Reply with ONLY ONE WORD from the list above. No explanations."
                )
            else:
                prompt = (
                    "Classify into ONE of these words: EMERGENCY, MEDICATION, NUTRITION, RISK, ASHA, CARE\n"
                    f"Message: \"{message[:300]}\"\n"
                    "Reply with ONLY ONE WORD from the list above. No explanations."
                )

            # Use Groq for classification to save tokens & latency
            if GROQ_AVAILABLE and groq_client:
                classify_model = os.getenv('GROQ_MODEL_NAME_FAST', 'llama-3.1-8b-instant')
                response = groq_client.chat.completions.create(
                    model=classify_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10,
                )
                category = response.choices[0].message.content.strip().upper()
            else:
                classify_model = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash-lite')
                response = gemini_client.models.generate_content(
                    model=classify_model,
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

            # Robust matching: find the first keyword that appears in the response
            for key, agent in category_map.items():
                if key in category:
                    logger.info(f"🤖 AI classified: {agent.value}")
                    return agent

            logger.warning(f"⚠️ Unmapped AI classification category: '{category}'")
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
        """Fallback response using Groq/Gemini directly — with full safety guardrails."""
        if not GROQ_AVAILABLE and not GEMINI_AVAILABLE:
            return (
                "⚠️ I'm sorry, I'm having trouble processing your request right now. "
                "Please try again in a moment or contact your healthcare provider if urgent."
            )

        try:
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

            preferred_language = mother_context.get('preferred_language', 'en')

            system_prompt = (
                f"CRITICAL SAFETY RULES — you MUST follow these:\n"
                f"1. Strictly follow WHO and NHM India guidelines. Reply ONLY in {preferred_language}.\n"
                f"2. NEVER prescribe medications or dosages — only a doctor can do that.\n"
                f"3. NEVER recommend stopping prescribed medications.\n"
                f"4. NEVER discuss or predict the sex/gender of the baby (illegal under PCPNDT Act, India).\n"
                f"5. NEVER recommend unsafe home remedies (castor oil, papaya for induction, etc.).\n"
                f"6. If symptoms sound urgent (bleeding, seizures, severe pain, unconsciousness), "
                f"IMMEDIATELY advise calling 108 (ambulance) or going to the nearest hospital.\n"
                f"7. When giving medical advice, cite the source: [SOURCE: WHO/NHM/IMNCI/IAP]\n"
                f"8. If you are not confident about something, say so honestly and advise consulting a doctor.\n"
                f"9. Ask 1-2 clarifying questions before giving advice.\n\n"
                f"You are a maternal health assistant for: {context_str}.{memory_hint}\n\n"
                f"Reply empathetically. Include [SOURCE: guideline] for any medical advice."
            )

            if GROQ_AVAILABLE and groq_client:
                model_name = os.getenv('GROQ_MODEL_NAME_SMART', 'llama-3.3-70b-versatile')
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                import re
                raw = response.choices[0].message.content
                cleaned = re.sub(r'\*{1,3}|_{1,3}|`{1,3}', '', raw)
                cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'^\|.*\|$', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'^-{3,}\s*$', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
            elif GEMINI_AVAILABLE and gemini_client:
                model_name = (
                    os.getenv('GEMINI_SFT_MODEL')
                    or os.getenv('GEMINI_MODEL_NAME')
                    or 'gemini-2.0-flash'
                )
                full_prompt = system_prompt + f"\n\nQuestion: {message}"
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                import re
                raw = response.text
                cleaned = re.sub(r'\*{1,3}|_{1,3}|`{1,3}', '', raw)
                cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'^\|.*\|$', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'^-{3,}\s*$', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
            else:
                return "AI service is unavailable."

            # ===== POST-VALIDATION (was previously bypassed for fallback) =====
            try:
                try:
                    from backend.services.response_validator import validate_response, ValidationSeverity
                except ImportError:
                    from services.response_validator import validate_response, ValidationSeverity

                validation_context = {
                    'query': message,
                    'mother_id': mother_context.get('id'),
                    'agent_type': 'fallback'
                }
                result = validate_response(cleaned, validation_context, 'fallback')

                if result.severity == ValidationSeverity.CRITICAL:
                    logger.warning(f"🚨 Fallback response BLOCKED: {result.issues}")
                    return result.modified_response
                elif result.severity == ValidationSeverity.WARNING:
                    cleaned = result.modified_response or cleaned
            except Exception as ve:
                logger.error(f"Fallback validation error: {ve}")

            return cleaned

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