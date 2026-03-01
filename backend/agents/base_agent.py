"""
Aanchal AI - Base Agent Class
All specialized agents inherit from this base class
"""

import os
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Explicitly load .env from the backend directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Use shared Gemini key rotator (supports up to 3 API keys)
try:
    from services.gemini_rotator import gemini_rotator
    gemini_client = gemini_rotator  # keep same variable name for compatibility
    GEMINI_AVAILABLE = gemini_rotator.is_available
    GEMINI_MODEL_NAME = os.getenv('GEMINI_SFT_MODEL') or os.getenv('GEMINI_MODEL_NAME') or 'gemini-2.0-flash'
except ImportError:
    try:
        from backend.services.gemini_rotator import gemini_rotator
        gemini_client = gemini_rotator
        GEMINI_AVAILABLE = gemini_rotator.is_available
        GEMINI_MODEL_NAME = os.getenv('GEMINI_SFT_MODEL') or os.getenv('GEMINI_MODEL_NAME') or 'gemini-2.0-flash'
    except ImportError:
        gemini_client = None
        GEMINI_AVAILABLE = False
        GEMINI_MODEL_NAME = 'gemini-2.0-flash'

# Import Groq
groq_client = None
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_groq_api_key_here":
        groq_client = Groq(api_key=GROQ_API_KEY)
        GROQ_AVAILABLE = True
    else:
        GROQ_AVAILABLE = False
except Exception:
    GROQ_AVAILABLE = False

# Select model via env hook
GROQ_MODEL_NAME = (
    os.getenv("GROQ_MODEL_NAME_SMART")
    or "llama-3.3-70b-versatile"
)

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


class _GroqModelWrapper:
    """Wrapper for Groq API to mimic Gemini's generate_content interface"""

    def __init__(self, client, model_name: str):
        self._client = client
        self._model_name = model_name

    def generate_content(self, prompt: str):
        # Split prompt into system + user parts at the User Question separator if present
        if "\nUser Question:" in prompt:
            parts = prompt.split("\nUser Question:", 1)
            system_content = parts[0].strip()
            user_content = "User Question:" + parts[1].strip()
        else:
            system_content = "You are a helpful maternal and child health assistant."
            user_content = prompt

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        class CompatResponse:
            def __init__(self, text):
                self.text = text
        return CompatResponse(response.choices[0].message.content)


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_name: str, agent_role: str):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.client = None
        self.model = None
        self.model_name = GROQ_MODEL_NAME  # Default to Groq

        # Prefer Groq for text generation (faster, no quota issues)
        if GROQ_AVAILABLE and groq_client:
            try:
                self.client = groq_client
                self.model = _GroqModelWrapper(groq_client, GROQ_MODEL_NAME)
                self.model_name = GROQ_MODEL_NAME
                logger.info(f"✅ {agent_name} initialized with Groq model: {GROQ_MODEL_NAME}")
            except Exception as e:
                logger.error(f"❌ {agent_name} failed to initialize Groq: {e}")

        # Fallback to Gemini only if Groq is unavailable
        if not self.client and GEMINI_AVAILABLE and gemini_client:
            try:
                self.client = gemini_client
                self.model = _GeminiModelWrapper(gemini_client, GEMINI_MODEL_NAME)
                self.model_name = GEMINI_MODEL_NAME
                logger.info(f"✅ {agent_name} initialized with fallback Gemini model: {GEMINI_MODEL_NAME}")
            except Exception as e:
                logger.error(f"❌ {agent_name} failed to initialize Gemini: {e}")

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
            
            system_message_content = f"""
You are a specialized maternal and child health assistant for the SantanRaksha / MatruRaksha system.
Reply EXCLUSIVELY in {preferred_language}. DO NOT mix languages.

ABSOLUTE SAFETY RULES (NEVER VIOLATE):
1. NEVER prescribe specific medication doses — only a doctor can do that.
2. NEVER recommend stopping prescribed medications.
3. NEVER discuss baby's sex/gender — illegal under PCPNDT Act, India.
4. NEVER suggest unsafe home remedies (castor oil, unripe papaya, alcohol rubs).
5. For URGENT symptoms (heavy bleeding, seizures, high fever, unconscious) — immediately advise calling 108 or going to the nearest hospital.
6. NEVER hallucinate data — if child vaccination dates/weights/ages exist in the records below, use those EXACT values. If data is missing, say so clearly.

ANSWER FORMAT RULES (STRICTLY FOLLOW):
- Be CONCISE and SPECIFIC. Do not pad with generic health advice.
- Write in short paragraphs (2-4 sentences each). NO unnecessary bullet-point lists.
- Use CAPITAL LETTERS or plain words for emphasis (e.g. 38.5 C, 6 months, OPV-2). Do NOT use asterisks, underscores, hashes, or any other markdown formatting.
- If you give numbered steps, keep them short (max 4-5 items).
- End EVERY response with a Sources line and a disclaimer, like this:

  Sources:
  - [WHO](https://www.who.int/)
  - [NHM India](https://nhm.gov.in/)

  Note: This guidance is for informational purposes. Always consult your healthcare provider for personalized advice. Clinical guidelines referenced: IMNCI, WHO, IAP 2023.

- DO NOT ask multiple clarifying questions. If you absolutely need one, ask only ONE short question at the end.
{memory_section}
CULTURAL SENSITIVITY:
- Never assume dietary preferences based on name/region/religion.
- Handle sensitive disclosures (violence, abuse) with care — provide helpline 181.
- Acknowledge traditional practices respectfully, then give evidence-based guidance.

{system_prompt}

=== PATIENT DATABASE RECORDS (USE THESE — DO NOT GUESS OR HALLUCINATE) ===
{context_info}
=== END OF RECORDS ===

IMPORTANT: If the records contain specific child vaccination dates, growth measurements, or pending vaccines — you MUST cite those EXACT values in your response.
If a specific record does NOT exist, answer generically and say data is not yet available.
"""
            full_prompt = system_message_content + f"\nUser Question: {query}\n\nResponse (ask clarifying questions if needed, cite [SOURCE: guideline] for all medical advice):"
            response = self.model.generate_content(full_prompt)
            raw_response = response.text.strip()

            # Strip ALL markdown symbols so Telegram shows clean plain text
            import re
            def clean_markdown(text: str) -> str:
                text = re.sub(r'\*{1,3}', '', text)          # remove *, **, ***
                text = re.sub(r'_{1,3}', '', text)           # remove _, __, ___
                text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # remove ### headers
                text = re.sub(r'`{1,3}', '', text)           # remove backticks
                text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)  # remove --- dividers
                text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)    # remove markdown tables
                text = re.sub(r'\n{3,}', '\n\n', text)      # collapse excess blank lines
                return text.strip()

            cleaned_response = clean_markdown(raw_response)
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

