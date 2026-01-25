"""
Pregnancy History Service
Fetches mother's pregnancy data for postnatal AI context

This service provides pregnancy history to postnatal agents so they can give
informed, personalized recommendations based on the mother's pregnancy journey.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Supabase client
try:
    from services.supabase_service import supabase
except ImportError:
    try:
        from backend.services.supabase_service import supabase
    except ImportError:
        supabase = None


async def get_pregnancy_history_context(mother_id: str) -> Dict[str, Any]:
    """
    Fetch complete pregnancy history for AI context
    Used by postnatal agents to provide informed recommendations
    
    Args:
        mother_id: Mother's UUID
    
    Returns:
        Dictionary with pregnancy profile, reports, risks, medications
    """
    if not supabase:
        logger.error("Supabase not available")
        return _empty_history()
    
    try:
        # 1. Get mother's pregnancy profile
        mother_result = supabase.table('mothers').select('*').eq('id', mother_id).single().execute()
        
        if not mother_result.data:
            logger.warning(f"Mother {mother_id} not found")
            return _empty_history()
        
        mother = mother_result.data
        
        # 2. Get ANC reports (risk assessments, complications)
        try:
            reports_result = supabase.table('user_reports')\
                .select('*')\
                .eq('mother_id', mother_id)\
                .order('report_date', desc=True)\
                .limit(15)\
                .execute()
            reports = reports_result.data or []
        except Exception as e:
            logger.warning(f"Could not fetch reports: {e}")
            reports = []
        
        # 3. Get recent chat history for pregnancy concerns (optional)
        pregnancy_concerns = []
        try:
            # Get conversation IDs from pregnancy period
            chats_result = supabase.table('chat_logs')\
                .select('conversation_id, created_at')\
                .eq('mother_id', mother_id)\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            
            if chats_result.data:
                # Could extract themes from chat history here
                # For now, just note that conversations exist
                pregnancy_concerns.append({
                    'count': len(chats_result.data),
                    'last_date': chats_result.data[0].get('created_at') if chats_result.data else None
                })
        except Exception as e:
            logger.warning(f"Could not fetch chat history: {e}")
        
        # Build comprehensive context
        context = {
            "mother_profile": mother,
            "pregnancy_reports": reports,
            "pregnancy_concerns": pregnancy_concerns,
            "risk_factors": [],
            "medications": [],
            "complications": [],
            "delivery_info": {}
        }
        
        # 4. Extract risk factors from reports
        for report in reports:
            analysis = report.get('analysis_result', {})
            if analysis:
                risk = analysis.get('risk_level', 'NORMAL')
                factors = analysis.get('risk_factors', [])
                
                if risk in ['HIGH', 'MEDIUM'] or factors:
                    context['risk_factors'].append({
                        'date': report.get('report_date'),
                        'risk_level': risk,
                        'factors': factors,
                        'report_type': report.get('report_type', 'unknown')
                    })
        
        # 5. Extract delivery information
        context['delivery_info'] = {
            'delivery_date': mother.get('delivery_date'),
            'delivery_type': mother.get('delivery_type'),
            'delivery_hospital': mother.get('delivery_hospital'),
            'gestational_age_weeks': mother.get('gestational_age_weeks'),
            'delivery_complications': mother.get('delivery_complications', [])
        }
        
        logger.info(f"✅ Fetched pregnancy history for {mother_id}: {len(reports)} reports, {len(context['risk_factors'])} risk factors")
        return context
        
    except Exception as e:
        logger.error(f"Error fetching pregnancy history: {e}")
        return _empty_history()


def format_history_for_prompt(history: Dict[str, Any]) -> str:
    """
    Format pregnancy history into LLM prompt text
    
    Args:
        history: Pregnancy history dictionary
    
    Returns:
        Formatted string for LLM prompt
    """
    mother = history.get('mother_profile', {})
    delivery = history.get('delivery_info', {})
    
    prompt = f"""
# Pregnancy History (MatruRaksha Records)

**Mother:** {mother.get('name', 'Unknown')} ({mother.get('age', '?')} years)
**BMI:** {mother.get('bmi', 'unknown')} kg/m²
**Obstetric History:** G{mother.get('gravida', '?')}P{mother.get('parity', '?')}
**Blood Group:** {mother.get('blood_group', 'unknown')}

## Delivery Details:
- Date: {delivery.get('delivery_date', 'not recorded')}
- Type: {delivery.get('delivery_type', 'unknown').title()}
- Hospital: {delivery.get('delivery_hospital', 'unknown')}
- Gestational Age: {delivery.get('gestational_age_weeks', '?')} weeks
"""
    
    # Add complications if any
    complications = delivery.get('delivery_complications', [])
    if complications:
        prompt += f"- Complications: {', '.join(complications)}\n"
    
    # Add risk factors
    risk_factors = history.get('risk_factors', [])
    if risk_factors:
        prompt += "\n## Risk Factors During Pregnancy:\n"
        for risk in risk_factors[:5]:  # Limit to top 5
            date = risk.get('date', 'unknown date')
            level = risk.get('risk_level', 'UNKNOWN')
            factors = risk.get('factors', [])
            
            if factors:
                prompt += f"- {date}: **{level}** - {', '.join(factors[:3])}\n"
            else:
                prompt += f"- {date}: {level} risk level\n"
    else:
        prompt += "\n## Risk Factors:\n- No major risk factors identified during pregnancy\n"
    
    # Add pregnancy summary
    reports_count = len(history.get('pregnancy_reports', []))
    prompt += f"\n## ANC Monitoring:\n"
    prompt += f"- Total reports analyzed: {reports_count}\n"
    
    if reports_count > 0:
        prompt += "- Regular monitoring and care throughout pregnancy\n"
    
    # Add note about using this data
    prompt += f"""
---
**IMPORTANT:** Use this pregnancy history as CONTEXT to provide personalized 
postnatal care. For example, if there was gestational diabetes, monitor for 
baby's blood sugar issues. If there was anemia, check for continued iron needs.
"""
    
    return prompt


def extract_key_risks(history: Dict[str, Any]) -> List[str]:
    """
    Extract key risk factors as a simple list
    
    Args:
        history: Pregnancy history dictionary
    
    Returns:
        List of key risk factor strings
    """
    risks = []
    
    for risk_item in history.get('risk_factors', []):
        factors = risk_item.get('factors', [])
        risks.extend(factors)
    
    # Deduplicate
    return list(set(risks))


def get_pregnancy_summary(history: Dict[str, Any]) -> str:
    """
    Get one-line pregnancy summary
    
    Args:
        history: Pregnancy history dictionary
    
    Returns:
        Brief summary string
    """
    mother = history.get('mother_profile', {})
    delivery = history.get('delivery_info', {})
    risks = extract_key_risks(history)
    
    summary_parts = []
    
    # Obstetric history
    g = mother.get('gravida')
    p = mother.get('parity')
    if g and p:
        summary_parts.append(f"G{g}P{p}")
    
    # Delivery type
    delivery_type = delivery.get('delivery_type')
    if delivery_type:
        summary_parts.append(delivery_type.upper())
    
    # Key risks
    if risks:
        summary_parts.append(f"Risks: {', '.join(risks[:2])}")
    else:
        summary_parts.append("Low-risk pregnancy")
    
    return " | ".join(summary_parts)


def _empty_history() -> Dict[str, Any]:
    """Return empty history structure"""
    return {
        "mother_profile": {},
        "pregnancy_reports": [],
        "pregnancy_concerns": [],
        "risk_factors": [],
        "medications": [],
        "complications": [],
        "delivery_info": {}
    }
