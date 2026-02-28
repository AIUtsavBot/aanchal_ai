"""
Aanchal AI - Base Agent Class
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

# Select model via env hook (supports fine-tuned model names)
GEMINI_MODEL_NAME = (
    os.getenv("GEMINI_SFT_MODEL")
    or os.getenv("GEMINI_MODEL_NAME")
    or "gemini-2.0-flash"
)


class _GeminiModelWrapper:
    """Wrapper to provide backwards-compatible generate_content() interface"""

    def __init__(self, client, model_name: str):
        self._client = client
        self._model_name = model_name

    def generate_content(self, prompt: str):
        """Generate content using the new client API but old-style interface"""
        return self._client.models.generate_content(
            model=self._model_name,
            contents=prompt
        )


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_name: str, agent_role: str):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.client = None
        self.model = None  # For backwards compatibility with agents using self.model
        self.model_name = GEMINI_MODEL_NAME

        if GEMINI_AVAILABLE and gemini_client:
            try:
                self.client = gemini_client
                # Create a model wrapper for agents that use self.model directly
                self.model = _GeminiModelWrapper(gemini_client, GEMINI_MODEL_NAME)
                logger.info(f"✅ {agent_name} initialized with Gemini model: {GEMINI_MODEL_NAME}")
            except Exception as e:
                logger.error(f"❌ {agent_name} failed to initialize: {e}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    async def build_context(self, mother_id: Any) -> Dict[str, Any]:
        """Build context using optimized async builder"""
        try:
            # We need a supabase client. 
            # In a real app we might pass it in, but here we can instantiate one or import usage.
            # Best is to reuse the singleton from services/supabase_service if possible, 
            # but creating a client is cheap if lightweight. 
            # Ideally context_builder takes a client.
            try:
                from backend.services.supabase_service import supabase
                from backend.context_builder import build_holistic_context_async
            except ImportError:
                from services.supabase_service import supabase
                from context_builder import build_holistic_context_async
                
            return await build_holistic_context_async(mother_id, supabase)
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return {"context_text": f"Error loading context: {e}", "raw_data": {}}
    
    async def process_query(
        self,
        query: str,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]],
        language: str = 'en'
    ) -> str:
        """Process a query and return validated response"""
        if not self.client:
            return (
                f"⚠️ {self.agent_name} is currently unavailable. "
                "Please try again later or contact support."
            )
        
        try:
            # Build full prompt with citation requirements
            system_prompt = self.get_system_prompt()
            
            # Context building is now async and returns a dict
            context_result = await self.build_context(mother_context.get('id'))
            context_info = context_result.get('context_text', '')
            
            # Removed RAG implementation to use built-in Google Search Grounding instead
            rag_evidence = ""
            
            preferred_language = language or mother_context.get('preferred_language', 'en')
            
            # Enhanced prompt with citation requirements
            # Include conversation memory context if available
            follow_up_prompt = mother_context.get('follow_up_prompt', '')
            past_symptoms = mother_context.get('past_symptoms', [])
            
            memory_section = ""
            if follow_up_prompt:
                memory_section = f"\n{follow_up_prompt}\n"
            elif past_symptoms:
                memory_section = f"\n⚠️ PAST HISTORY: This mother previously reported: {', '.join(past_symptoms[:5])}\n"
            
            full_prompt = f"""
CRITICAL: Strictly follow WHO and NHM India guidelines. If High Risk, recommend hospital. Reply ONLY in {preferred_language}.

ABSOLUTE SAFETY RULES (NEVER VIOLATE):
1. NEVER prescribe medications or dosages — only a doctor can do that.
2. NEVER recommend stopping prescribed medications or IFA tablets.
3. NEVER discuss or predict the sex/gender of the baby — this is ILLEGAL under the PCPNDT Act, 1994 (India). If asked, respond: "I cannot discuss this. Sex determination is prohibited by law in India."
4. NEVER recommend unsafe home remedies: castor oil for labor, unripe papaya, alcohol rubs, misoprostol without doctor.
5. If symptoms sound urgent (bleeding, seizures, severe pain, unconsciousness, high fever), IMMEDIATELY advise calling 108 (ambulance) or 102 (maternal helpline).

CITATION AND WEB SEARCH REQUIREMENT:
1. You MUST use your search tools to scrape the internet for the most accurate and up-to-date WHO, NHM, and current medical guidelines from trusted government/medical sources to answer the user's question.
2. At the end of your response, you MUST attach the exact website source/URL from where you provided the information, so the user can verify it. Example: [Source: https://www.who.int/... ]
{memory_section}
QUESTIONING PROTOCOL (IMPORTANT):
1. If past history is shown above, ACKNOWLEDGE it and ask if current issue is related
2. MANDATORY: Whether this is a NEW topic or RECURRING, you MUST ask 1-2 clarifying questions before giving advice:
   - Duration: "कितने दिन से?" / "किती दिवसांपासून?"
   - Severity: "कितना तेज़?" / "किती तीव्र?"
   - Triggers: What makes it better/worse?
3. If this is a recurring issue, ask if previous advice helped
4. Gather information FIRST, then provide advice

CULTURAL SENSITIVITY & BIAS PREVENTION:
- NEVER assume dietary preferences based on the mother's name, region, or religion
- Respect vegetarian, vegan, Jain, and halal dietary needs — always offer alternatives
- Do NOT dismiss traditional practices outright — acknowledge them, then provide evidence-based correction if needed
- Handle domestic violence/abuse disclosures sensitively — provide helpline 181 (Women Helpline)
- Use inclusive, non-judgmental language

CONFIDENCE & UNCERTAINTY:
- If you are NOT confident about a medical fact, say: "I am not fully sure about this — please confirm with your doctor."
- If the question is outside your expertise area, say: "This is outside my specialty. Let me help you find the right resource."
- NEVER make up clinical values, drug dosages, or threshold numbers — only use values from established guidelines

{system_prompt}

{context_info}

User Question: {query}

Response (ask clarifying questions if needed, cite [SOURCE: guideline] for all medical advice):
"""
            
            # Generate response using new client API with Google Search Grounding
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={'tools': [{'google_search': {}}]}
            )
            
            # Clean response
            cleaned_response = response.text.strip()
            
            # ==================== POST-VALIDATION ====================
            # Validate response against clinical rules before returning
            try:
                try:
                    from backend.services.response_validator import validate_response, ValidationSeverity
                except ImportError:
                    from services.response_validator import validate_response, ValidationSeverity
                
                # Build validation context
                validation_context = {
                    'query': query,
                    'age_months': mother_context.get('child_age_months') or mother_context.get('age_months', 12),
                    'mother_id': mother_context.get('id'),
                    'agent_type': self.agent_name
                }
                
                validation_result = validate_response(
                    cleaned_response, 
                    validation_context, 
                    self.agent_name
                )
                
                if validation_result.severity == ValidationSeverity.CRITICAL:
                    # Block response, use safe fallback
                    logger.warning(
                        f"🚨 {self.agent_name} response BLOCKED: {validation_result.issues}"
                    )
                    return validation_result.modified_response
                
                elif validation_result.severity == ValidationSeverity.WARNING:
                    # Add disclaimer to response
                    logger.info(
                        f"⚠️ {self.agent_name} response has warnings: {validation_result.issues}"
                    )
                    cleaned_response = validation_result.modified_response or cleaned_response
                
                # Log citation status
                if validation_result.citations_missing:
                    logger.info(f"📚 {self.agent_name}: No citations found in response")
                else:
                    logger.info(
                        f"📚 {self.agent_name}: Citations found: {validation_result.citations_found}"
                    )
                    
            except ImportError as ie:
                # Validator not available - log and continue
                logger.warning(f"Response validator not available: {ie}")
            except Exception as ve:
                # Validation error - log but don't fail the response
                logger.error(f"Response validation error: {ve}")
            
            logger.info(f"✅ {self.agent_name} processed query successfully")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} error: {e}")
            return (
                f"I apologize, but I encountered an issue processing your request. "
                f"Please try rephrasing your question or contact your healthcare provider if urgent."
            )

