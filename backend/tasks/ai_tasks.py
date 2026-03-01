"""
AI Analysis Background Tasks
Offload AI-intensive operations to background workers
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def analyze_risk_async(self, mother_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task for AI risk analysis
    
    Args:
        mother_id: Mother's ID
        assessment_data: Assessment parameters
    
    Returns:
        Risk analysis result
    """
    task_id = self.request.id
    logger.info(f"🤖 Starting risk analysis for mother {mother_id} (task: {task_id})")
    
    try:
        # Import here to avoid circular imports
        from services.cache_service import cache
        
        # Check if already cached
        cache_key = f"risk:analysis:{mother_id}"
        cached = cache.get(cache_key) if cache else None
        if cached:
            logger.info(f"📊 Using cached risk analysis for {mother_id}")
            return cached
        
        # Perform AI analysis
        result = _perform_risk_analysis(assessment_data)
        
        # Cache result for 1 hour
        if cache:
            cache.set(cache_key, result, ttl_seconds=3600)
        
        # Store in database (async would be better but Celery is sync)
        _save_risk_result(mother_id, result)
        
        logger.info(f"✅ Risk analysis complete for {mother_id}: {result.get('risk_level', 'UNKNOWN')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Risk analysis failed for {mother_id}: {e}")
        
        # Check if we've exhausted retries
        if self.request.retries >= self.max_retries:
            logger.error(f"❌ Max retries exceeded for {mother_id}")
            return {"status": "failed", "error": str(e), "mother_id": mother_id}
        
        # Re-raise for retry
        raise


def _perform_risk_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform AI risk analysis using Groq"""
    try:
        # Try to use Groq for analysis
        from groq import Groq
        
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key or groq_key == "gsk_your_groq_api_key_here":
            return _fallback_risk_analysis(data)
        
        client = Groq(api_key=groq_key)
        
        prompt = f"""Analyze this maternal health data and provide a risk assessment:
        
        Data: {json.dumps(data)}
        
        Respond with JSON containing:
        - risk_level: HIGH, MODERATE, or LOW
        - risk_factors: list of identified risk factors
        - recommendations: list of recommendations
        - confidence: confidence score 0-100
        """
        
        model_name = os.getenv("GROQ_MODEL_NAME_SMART", "llama-3.3-70b-versatile")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse response
        text = response.choices[0].message.content
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        elif text.strip().startswith('{'):
            return json.loads(text)
        
        return _fallback_risk_analysis(data)
        
    except Exception as e:
        logger.warning(f"⚠️ Groq analysis failed, using fallback: {e}")
        return _fallback_risk_analysis(data)


def _fallback_risk_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based fallback risk analysis"""
    risk_factors = []
    risk_score = 0
    
    # Check BP
    systolic = data.get("blood_pressure_systolic", 0)
    diastolic = data.get("blood_pressure_diastolic", 0)
    
    if systolic >= 140 or diastolic >= 90:
        risk_factors.append("High blood pressure")
        risk_score += 30
    
    # Check age
    age = data.get("age", 25)
    if age < 18 or age > 35:
        risk_factors.append("Age risk factor")
        risk_score += 15
    
    # Check danger signs
    danger_signs = ["fever", "excessive_bleeding", "foul_discharge", "convulsions"]
    for sign in danger_signs:
        if data.get(sign, False):
            risk_factors.append(sign.replace("_", " ").title())
            risk_score += 25
    
    # Determine risk level
    if risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "recommendations": _get_recommendations(risk_level, risk_factors),
        "confidence": 75,
        "analysis_type": "rule_based"
    }


def _get_recommendations(risk_level: str, risk_factors: list) -> list:
    """Get recommendations based on risk level"""
    recommendations = []
    
    if risk_level == "HIGH":
        recommendations.append("Seek immediate medical attention")
        recommendations.append("Contact assigned doctor immediately")
    elif risk_level == "MODERATE":
        recommendations.append("Schedule a follow-up appointment within 48 hours")
        recommendations.append("Monitor symptoms closely")
    
    if "High blood pressure" in risk_factors:
        recommendations.append("Reduce salt intake")
        recommendations.append("Take prescribed BP medication regularly")
    
    return recommendations


def _save_risk_result(mother_id: str, result: Dict[str, Any]):
    """Save risk analysis result to database"""
    try:
        from supabase import create_client
        
        supabase = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", "")
        )
        
        supabase.table("risk_assessments").insert({
            "mother_id": mother_id,
            "risk_level": result.get("risk_level", "UNKNOWN"),
            "risk_score": result.get("risk_score", 0),
            "risk_factors": result.get("risk_factors", []),
            "recommendations": result.get("recommendations", []),
            "analysis_type": result.get("analysis_type", "unknown"),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"💾 Risk result saved for mother {mother_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save risk result: {e}")


@shared_task(bind=True, max_retries=2)
def process_agent_query_async(
    self,
    query: str,
    mother_context: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """
    Background task for AI agent query processing
    
    Args:
        query: User's query
        mother_context: Mother's context data
        session_id: Session identifier
    
    Returns:
        Agent response
    """
    task_id = self.request.id
    logger.info(f"🤖 Processing agent query (task: {task_id})")
    
    try:
        # Import orchestrator
        try:
            from agents.orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
        except ImportError:
            from backend.agents.orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
        
        if not orchestrator:
            return {
                "status": "error",
                "response": "AI agents not available",
                "session_id": session_id
            }
        
        # Process query
        response = orchestrator.process_query(query, mother_context, session_id)
        
        logger.info(f"✅ Agent query processed for session {session_id}")
        
        return {
            "status": "success",
            "response": response,
            "session_id": session_id,
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"❌ Agent query failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "session_id": session_id
        }


@shared_task
def cleanup_old_results():
    """Periodic task to cleanup old analysis results"""
    logger.info("🧹 Cleaning up old analysis results...")
    
    try:
        from services.cache_service import cache
        
        # Clear old risk analysis cache entries
        if cache:
            deleted = cache.delete_pattern("risk:analysis:*")
            logger.info(f"🧹 Deleted {deleted} old cache entries")
        
        return {"status": "success", "deleted": deleted if cache else 0}
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return {"status": "error", "error": str(e)}


# ==================== TASK STATUS HELPERS ====================

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a background task"""
    from tasks.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() and result.successful() else None,
        "error": str(result.result) if result.ready() and not result.successful() else None
    }
