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
gemini_client = None
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
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
        self.client = None
        self.model_name = GEMINI_MODEL_NAME
        
        if GEMINI_AVAILABLE and gemini_client:
            try:
                self.client = gemini_client
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
        """Process a query and return response"""
        if not self.client:
            return (
                f"⚠️ {self.agent_name} is currently unavailable. "
                "Please try again later or contact support."
            )
        
        try:
            # Build full prompt
            system_prompt = self.get_system_prompt()
            
            # Context building is now async and returns a dict
            context_result = await self.build_context(mother_context.get('id'))
            context_info = context_result.get('context_text', '')
            
            preferred_language = language or mother_context.get('preferred_language', 'en')
            
            full_prompt = f"""
CRITICAL: Strictly follow WHO and NHM India guidelines. If High Risk, recommend hospital. Reply ONLY in {preferred_language}.

{system_prompt}

{context_info}

User Question: {query}

Response:
"""
            
            # Generate response using new client API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
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
