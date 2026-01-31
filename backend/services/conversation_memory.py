"""
Intelligent Conversation Memory Service
Uses Supabase pgvector for semantic search + Gemini for embeddings/extraction

Features:
- Extract symptoms/topics from messages using Gemini
- Semantic search for similar past conversations
- Build follow-up context for AI responses
- Store conversation summaries with embeddings
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Initialize clients
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    gemini_client = None

try:
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None


@dataclass
class ConversationContext:
    """Context from past conversations for follow-up"""
    has_history: bool
    similar_conversations: List[Dict]
    follow_up_prompt: str
    extracted_topics: List[str]
    past_symptoms: List[str]
    past_advice: List[str]


class ConversationMemoryService:
    """
    Intelligent conversation memory using Supabase pgvector.
    No external RAG service needed - uses Gemini for embeddings.
    """
    
    def __init__(self):
        self.db = supabase
        self.gemini = gemini_client
        self.embedding_model = "text-embedding-004"  # Gemini embedding model
        self.embedding_dimensions = 768
        
    async def extract_topics_and_symptoms(self, message: str, language: str = "auto") -> Dict[str, Any]:
        """
        Use Gemini to extract symptoms, topics, and intent from a message.
        Works with Hindi, Marathi, and English.
        """
        if not self.gemini:
            return {"topics": [], "symptoms": [], "intent": "general", "severity": "low"}
        
        try:
            prompt = f"""Analyze this health-related message and extract structured information.
The message may be in Hindi, Marathi, or English.

Message: "{message}"

Return ONLY valid JSON:
{{
    "topics": ["list of health topics discussed, e.g., headache, nutrition, pregnancy"],
    "symptoms": ["list of symptoms mentioned, e.g., headache, fever, nausea"],
    "intent": "question|complaint|update|emergency|greeting",
    "severity": "low|medium|high|emergency",
    "duration_mentioned": "e.g., 2 days, 1 week, or null if not mentioned",
    "body_parts": ["any body parts mentioned"],
    "medications_mentioned": ["any medicines/treatments mentioned"],
    "food_mentioned": ["any foods/drinks mentioned"]
}}
"""
            response = self.gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            result = json.loads(response.text.strip())
            logger.info(f"📊 Extracted topics: {result.get('topics', [])}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return {"topics": [], "symptoms": [], "intent": "general", "severity": "low"}
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector using Gemini for semantic search.
        """
        if not self.gemini:
            return None
            
        try:
            # Use Gemini's embedding API
            response = self.gemini.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            
            # Extract embedding from response
            if hasattr(response, 'embeddings') and response.embeddings:
                return response.embeddings[0].values
            elif hasattr(response, 'embedding'):
                return response.embedding.values
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def search_similar_conversations(
        self, 
        mother_id: str, 
        query: str,
        topics: List[str] = None,
        limit: int = 5,
        days_back: int = 90
    ) -> List[Dict]:
        """
        Search for similar past conversations using:
        1. Semantic similarity (pgvector) if available
        2. Fallback to topic/keyword matching
        """
        if not self.db:
            return []
        
        similar = []
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        try:
            # Method 1: Try semantic search with pgvector
            embedding = await self.get_embedding(query)
            
            if embedding:
                try:
                    # Use Supabase RPC for vector similarity search
                    result = self.db.rpc(
                        'search_similar_conversations',
                        {
                            'query_embedding': embedding,
                            'mother_id_param': str(mother_id),
                            'match_threshold': 0.7,
                            'match_count': limit
                        }
                    ).execute()
                    
                    if result.data:
                        similar = result.data
                        logger.info(f"🔍 Found {len(similar)} similar conversations via semantic search")
                        return similar
                except Exception as vec_err:
                    logger.debug(f"Vector search not available: {vec_err}")
            
            # Method 2: Fallback to topic-based search
            if topics:
                # Search in conversation_summaries by topics
                result = self.db.table("conversation_summaries")\
                    .select("*")\
                    .eq("mother_id", str(mother_id))\
                    .gte("created_at", cutoff_date)\
                    .order("created_at", desc=True)\
                    .limit(limit * 2)\
                    .execute()
                
                if result.data:
                    # Filter by topic overlap
                    for conv in result.data:
                        conv_topics = conv.get('topics', [])
                        if isinstance(conv_topics, str):
                            try:
                                conv_topics = json.loads(conv_topics)
                            except:
                                conv_topics = []
                        
                        # Check topic overlap
                        overlap = set(t.lower() for t in topics) & set(t.lower() for t in conv_topics)
                        if overlap:
                            conv['topic_overlap'] = list(overlap)
                            similar.append(conv)
                    
                    similar = similar[:limit]
            
            # Method 3: Search telegram_logs for keyword matches
            if not similar and topics:
                keywords = topics[:3]  # Top 3 topics
                for keyword in keywords:
                    result = self.db.table("telegram_logs")\
                        .select("*")\
                        .eq("mother_id", str(mother_id))\
                        .ilike("message_content", f"%{keyword}%")\
                        .gte("created_at", cutoff_date)\
                        .order("created_at", desc=True)\
                        .limit(5)\
                        .execute()
                    
                    if result.data:
                        similar.extend(result.data)
                
                # Deduplicate
                seen = set()
                unique = []
                for conv in similar:
                    conv_id = conv.get('id')
                    if conv_id not in seen:
                        seen.add(conv_id)
                        unique.append(conv)
                similar = unique[:limit]
            
            logger.info(f"🔍 Found {len(similar)} similar conversations via topic/keyword search")
            return similar
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
    
    async def build_follow_up_context(
        self,
        mother_id: str,
        current_message: str,
        mother_name: str = ""
    ) -> ConversationContext:
        """
        Build context for intelligent follow-up responses.
        This is the main function called before generating AI response.
        """
        # Extract topics from current message
        extraction = await self.extract_topics_and_symptoms(current_message)
        topics = extraction.get('topics', [])
        symptoms = extraction.get('symptoms', [])
        intent = extraction.get('intent', 'general')
        
        # Handle greetings separately
        if intent == 'greeting':
            return ConversationContext(
                has_history=False,
                similar_conversations=[],
                follow_up_prompt="",
                extracted_topics=topics,
                past_symptoms=[],
                past_advice=[]
            )
        
        # Search for similar past conversations
        search_query = current_message
        if symptoms:
            search_query = " ".join(symptoms)
        elif topics:
            search_query = " ".join(topics)
        
        similar = await self.search_similar_conversations(
            mother_id=mother_id,
            query=search_query,
            topics=topics + symptoms,
            limit=5,
            days_back=90
        )
        
        # Build follow-up prompt
        follow_up_prompt = ""
        past_symptoms = []
        past_advice = []
        
        if similar:
            # Extract past symptoms and advice from similar conversations
            for conv in similar:
                conv_symptoms = conv.get('symptoms', [])
                if isinstance(conv_symptoms, str):
                    try:
                        conv_symptoms = json.loads(conv_symptoms)
                    except:
                        conv_symptoms = []
                past_symptoms.extend(conv_symptoms)
                
                advice = conv.get('advice_given', '')
                if advice:
                    past_advice.append(advice)
            
            past_symptoms = list(set(past_symptoms))[:5]
            past_advice = past_advice[:3]
            
            # Build context string for AI
            follow_up_prompt = self._build_history_prompt(
                similar_conversations=similar,
                current_symptoms=symptoms,
                past_symptoms=past_symptoms,
                past_advice=past_advice,
                mother_name=mother_name
            )
        
        return ConversationContext(
            has_history=bool(similar),
            similar_conversations=similar,
            follow_up_prompt=follow_up_prompt,
            extracted_topics=topics,
            past_symptoms=past_symptoms,
            past_advice=past_advice
        )
    
    def _build_history_prompt(
        self,
        similar_conversations: List[Dict],
        current_symptoms: List[str],
        past_symptoms: List[str],
        past_advice: List[str],
        mother_name: str = ""
    ) -> str:
        """Build the history context prompt for AI"""
        
        lines = []
        lines.append("=" * 40)
        lines.append("PAST CONVERSATION HISTORY (USE THIS!)")
        lines.append("=" * 40)
        
        name = mother_name or "this mother"
        
        # Add relevant past conversations
        for i, conv in enumerate(similar_conversations[:3], 1):
            date = conv.get('created_at', '')[:10]
            summary = conv.get('summary', conv.get('message_content', ''))[:200]
            topics = conv.get('topics', [])
            
            lines.append(f"\n📅 {date}:")
            lines.append(f"   Topics: {', '.join(topics) if topics else 'General'}")
            lines.append(f"   Summary: {summary}")
            
            advice = conv.get('advice_given', '')
            if advice:
                lines.append(f"   Advice given: {advice}")
        
        # Add instructions for AI
        lines.append("\n" + "=" * 40)
        lines.append("INSTRUCTIONS FOR THIS RESPONSE:")
        lines.append("=" * 40)
        
        if past_symptoms and current_symptoms:
            overlap = set(s.lower() for s in past_symptoms) & set(s.lower() for s in current_symptoms)
            if overlap:
                lines.append(f"⚠️ RECURRING ISSUE DETECTED: {', '.join(overlap)}")
                lines.append(f"   - Acknowledge you remember the previous discussion")
                lines.append(f"   - Ask if the current issue is related to the previous one")
                lines.append(f"   - Ask if previous advice helped")
        

        
        return "\n".join(lines)
    
    async def store_conversation_summary(
        self,
        mother_id: str,
        messages: List[Dict],
        topics: List[str] = None,
        symptoms: List[str] = None,
        advice_given: str = None
    ) -> bool:
        """
        Store a conversation summary for future retrieval.
        Called after a conversation exchange is complete.
        """
        if not self.db:
            return False
        
        try:
            # Create summary from messages
            summary = self._summarize_messages(messages)
            
            # Generate embedding for semantic search
            embedding_text = f"{summary} {' '.join(topics or [])} {' '.join(symptoms or [])}"
            embedding = await self.get_embedding(embedding_text)
            
            payload = {
                "mother_id": str(mother_id),
                "summary": summary,
                "topics": json.dumps(topics or []),
                "symptoms": json.dumps(symptoms or []),
                "advice_given": advice_given,
                "created_at": datetime.now().isoformat()
            }
            
            # Add embedding if available
            if embedding:
                payload["embedding"] = embedding
            
            self.db.table("conversation_summaries").insert(payload).execute()
            logger.info(f"💾 Stored conversation summary for mother {mother_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing conversation summary: {e}")
            return False
    
    def _summarize_messages(self, messages: List[Dict]) -> str:
        """Create a brief summary from message list"""
        if not messages:
            return ""
        
        parts = []
        for msg in messages[-5:]:  # Last 5 messages
            role = msg.get('role', msg.get('message_type', 'user'))
            content = msg.get('content', msg.get('message_content', ''))[:100]
            parts.append(f"{role}: {content}")
        
        return " | ".join(parts)


# Global instance
conversation_memory = ConversationMemoryService()


# Convenience functions for easy import
async def get_follow_up_context(mother_id: str, message: str, mother_name: str = "") -> ConversationContext:
    """Get conversation context with past history for follow-up questions"""
    return await conversation_memory.build_follow_up_context(mother_id, message, mother_name)


async def extract_message_info(message: str) -> Dict[str, Any]:
    """Extract symptoms, topics, and intent from a message"""
    return await conversation_memory.extract_topics_and_symptoms(message)


async def save_conversation(
    mother_id: str,
    messages: List[Dict],
    topics: List[str] = None,
    symptoms: List[str] = None,
    advice: str = None
) -> bool:
    """Save conversation summary for future retrieval"""
    return await conversation_memory.store_conversation_summary(
        mother_id, messages, topics, symptoms, advice
    )
