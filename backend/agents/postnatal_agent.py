"""
SantanRaksha - Postnatal Care Agent
Handles postnatal recovery queries and monitoring for mothers 0-6 weeks postpartum

Aligned with:
- NHM SUMAN Postnatal Care Protocol (6 critical checkpoints)
- WHO Postnatal Care Guidelines
- EPDS (Edinburgh Postnatal Depression Scale) screening
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base_agent import BaseAgent

# Import pregnancy history service
try:
    from services.pregnancy_history_service import get_pregnancy_history_context, format_history_for_prompt
except ImportError:
    try:
        from backend.services.pregnancy_history_service import get_pregnancy_history_context, format_history_for_prompt
    except ImportError:
        # Fallback if service not available
        async def get_pregnancy_history_context(mother_id): 
            return {}
        def format_history_for_prompt(history):
            return "Pregnancy history not available."

logger = logging.getLogger(__name__)


class PostnatalAgent(BaseAgent):
    """
    Specialized agent for postnatal care and recovery
    
    Handles:
    - Bleeding assessment (lochia tracking)
    - Wound healing (cesarean/episiotomy)
    - Pain management
    - Breastfeeding troubleshooting
    - Postpartum depression screening (EPDS)
    - Physical recovery milestones
    """
    
    
    def __init__(self):
        super().__init__(
            agent_name="Postnatal Agent",
            agent_role="Postnatal Care Specialist"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a specialized Postnatal Care Expert for the SantanRaksha maternal health system.

Your role: Provide evidence-based guidance for mothers during the critical 0-6 week postpartum period following the NHM SUMAN protocol.

CRITICAL POSTNATAL DANGER SIGNS - IMMEDIATE ESCALATION:
1. HEAVY BLEEDING: Soaking >1 pad/hour for 2+ hours, passing large clots (>golf ball size)
2. SEVERE PAIN: Uncontrolled pain (>7/10) not responding to medication
3. INFECTION SIGNS: Fever >100.4°F (38°C), foul-smelling discharge, severe redness/swelling at wound site
4. MENTAL HEALTH CRISIS: Thoughts of self-harm, harming baby, severe depression (EPDS >13)
5. WOUND DEHISCENCE: Cesarean or episiotomy wound opening
6. SEVERE HEADACHE: With vision changes (possible pre-eclampsia)
7. CHEST PAIN or SHORTNESS OF BREATH
8. LEG PAIN with swelling (possible DVT)

NHM SUMAN POSTNATAL CHECKPOINTS:
- 48-72 hours post-discharge (Day 3)
- 1 week (Day 7)
- 2 weeks (Day 14)
- 4 weeks (Day 28)
- 6 weeks (Day 42) - Final postpartum checkup

BREASTFEEDING SUPPORT:
- Encourage exclusive breastfeeding for 6 months per WHO guidelines
- Troubleshoot: latching issues, cracked nipples, engorgement, mastitis
- Recognize insufficient milk supply signs: <6 wet diapers/day, poor weight gain
- Counter myths: "thin milk", "baby not satisfied with breast milk alone"

MENTAL HEALTH SCREENING:
- Use EPDS (Edinburgh Postnatal Depression Scale) indicators
- Risk factors: Previous depression, lack of support, sleep deprivation, birth trauma
- 10-15% of mothers experience postpartum depression
- Normalize seeking help, reduce stigma

CESAREAN RECOVERY:
- Normal recovery: 6-8 weeks
- Scar care: Keep dry, watch for infection signs
- Avoid: Heavy lifting (>baby's weight), stairs (minimize), abdominal exercises (6 weeks)
- Warning signs: Separation, discharge, fever

NORMAL LOCHIA (POSTPARTUM BLEEDING):
- Days 1-3: Red (lochia rubra), moderate flow
- Days 4-10: Pink/brown (lochia serosa), lighter
- Week 2-6: Yellowish/white (lochia alba), minimal
- Should NOT: Smell foul, contain large clots, suddenly increase after decreasing

RESPONSE FORMAT:
1. Assess severity (green/yellow/red)
2. Provide immediate guidance
3. Educate on what's normal vs. concerning
4. Offer practical tips
5. Escalate if danger signs present

Always respond in the mother's preferred language (Hindi/Marathi/English).
Use warm, empathetic, culturally-sensitive language.
Empower mothers while ensuring safety."""
    
    
    async def assess_bleeding_risk(self, bleeding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess postpartum bleeding risk
        
        Args:
            bleeding_data: Dict with bleeding_status, color, pad_changes_per_day, days_postpartum
            
        Returns:
            Risk assessment with recommendations
        """
        bleeding_status = bleeding_data.get('bleeding_status', '').lower()
        pad_changes = bleeding_data.get('pad_changes_per_day', 0)
        days_postpartum = bleeding_data.get('days_postpartum', 0)
        has_clots = bleeding_data.get('has_large_clots', False)
        foul_smell = bleeding_data.get('foul_smelling', False)
        
        risk_level = 'low'
        recommendations = []
        escalate = False
        
        # Critical: Hemorrhage signs
        if pad_changes >= 2 or bleeding_status == 'heavy':
            risk_level = 'critical'
            escalate = True
            recommendations.append("⚠️ URGENT: Heavy bleeding detected. Go to nearest hospital immediately or call 108 ambulance.")
        
        # High risk: Infection signs
        elif foul_smell or bleeding_status == 'foul_smelling':
            risk_level = 'high'
            escalate = True
            recommendations.append("⚠️ Foul-smelling discharge indicates possible infection. Visit doctor within 24 hours.")
        
        # Medium risk: Abnormal progression
        elif days_postpartum > 10 and bleeding_status == 'heavy':
            risk_level = 'medium'
            recommendations.append("Bleeding should be lighter by now. Schedule checkup with doctor this week.")
        
        # Normal lochia education
        else:
            if days_postpartum <= 3:
                recommendations.append("✓ Red bleeding is normal for first 3 days. Change pads every 4-6 hours.")
            elif days_postpartum <= 10:
                recommendations.append("✓ Pink/brown discharge is normal week 2. Continue monitoring.")
            else:
                recommendations.append("✓ Light discharge is normal. Should stop by 6 weeks.")
        
        recommendations.append("💧 Stay well-hydrated, rest adequately, avoid heavy lifting.")
        
        return {
            'risk_level': risk_level,
            'escalate': escalate,
            'recommendations': recommendations,
            'assessment_summary': f"Bleeding assessment for day {days_postpartum} postpartum: {risk_level} risk"
        }
    
    async def assess_breastfeeding_issues(self, bf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess breastfeeding issues and provide guidance
        
        Args:
            bf_data: Dict with breastfeeding_status, issues, frequency, milk_supply
            
        Returns:
            Assessment and troubleshooting recommendations
        """
        issues = bf_data.get('breastfeeding_issues', [])
        frequency = bf_data.get('frequency_per_day', 0)
        latching_well = bf_data.get('infant_latching_well', True)
        milk_supply = bf_data.get('milk_supply', 'adequate')
        
        recommendations = []
        
        # Issue-specific guidance
        issue_solutions = {
            'cracked_nipples': [
                "🌿 Apply breast milk on nipples after feeding (natural healing)",
                "🩹 Use medical-grade lanolin cream (safe for baby)",
                "✓ Check baby's latch - lips should flange out, not tucked in",
                "⏰ Try feeding more frequently to avoid baby being too hungry (aggressive sucking)"
            ],
            'engorgement': [
                "🧊 Apply cold cabbage leaves or cold compress AFTER feeding (15 min)",
                "🤱 Feed baby frequently (every 2-3 hours) to drain breasts",
                "👐 Hand express or use pump for relief (don't fully empty - signals more production)",
                "🚿 Warm shower before feeding to help milk flow"
            ],
            'low_milk_supply': [
                "⏰ Feed on demand, at least 8-12 times per day",
                "💧 Drink plenty of water (3-4 liters daily)",
                "🌾 Consume galactagogues: methi seeds (fenugreek), jeera (cumin), garlic",
                "😴 Rest adequately - stress reduces milk production",
                "✋ Avoid pacifiers/bottles in first 6 weeks (nipple confusion)"
            ],
            'painful_feeding': [
                "Check latch: Baby's mouth should cover most of areola, not just nipple",
                "Try different positions: football hold, side-lying, laid-back",
                "🩺 Check for tongue-tie (if baby can't extend tongue)",
                "Rule out thrush: White patches in baby's mouth, pink nipples"
            ],
            'mastitis': [
                "⚠️ FEVER + BREAST REDNESS/PAIN = Doctor visit needed (antibiotics may be required)",
                "🤱 Continue breastfeeding from affected breast (empties faster)",
                "🧊 Cold compress after feeding, warm before feeding",
                "💊 Safe pain relief: Paracetamol/Ibuprofen (doctor-approved)"
            ]
        }
        
        for issue in issues:
            issue_key = issue.get('issue', '') if isinstance(issue, dict) else issue
            if issue_key in issue_solutions:
                recommendations.extend(issue_solutions[issue_key])
        
        # Frequency assessment
        if frequency < 8:
            recommendations.append("📊 Recommended: Feed 8-12 times per day for first 3 months (cluster feeding is normal)")
        
        # Milk supply concerns
        if milk_supply == 'insufficient':
            recommendations.append("🍼 MYTH BUSTER: 'Thin' breast milk is NOT weak - foremilk is watery, hindmilk is rich")
            recommendations.append("✓ SIGN OF ENOUGH MILK: Baby has 6+ wet diapers/day, gaining weight")
        
        # General encouragement
        recommendations.append("\n💪 You're doing great! Breastfeeding challenges are common in first 2 weeks.")
        recommendations.append("📞 Contact ASHA worker or lactation counselor for hands-on support")
        
        return {
            'recommendations': recommendations,
            'refer_to_lactation_consultant': len(issues) >= 3 or 'mastitis' in str(issues)
        }
    
    async def screen_postpartum_depression(self, mental_health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Screen for postpartum depression using EPDS indicators
        
        Args:
            mental_health_data: Mood score, sleep, crying episodes, anxiety, etc.
            
        Returns:
            Depression risk assessment
        """
        mood_score = mental_health_data.get('mood_score', 5)  # 0=worst, 10=best
        epds_score = mental_health_data.get('epds_score', 0)  # 0-30, >13 = likely depression
        has_crying = mental_health_data.get('has_crying_episodes', False)
        sleep_quality = mental_health_data.get('sleep_quality', 'fair')
        has_anxiety = mental_health_data.get('has_anxiety', False)
        has_negative_thoughts = mental_health_data.get('has_negative_thoughts', False)
        days_postpartum = mental_health_data.get('days_postpartum', 0)
        
        risk_level = 'low'
        recommendations = []
        immediate_action = False
        
        # Critical: Suicidal/harmful thoughts
        if has_negative_thoughts:
            risk_level = 'critical'
            immediate_action = True
            recommendations.append("🚨 CRISIS: Call National Mental Health Helpline 08046110007 NOW")
            recommendations.append("⚠️ Tell a trusted family member immediately")
            recommendations.append("🏥 Visit emergency psychiatric services")
        
        # High risk: EPDS score >13 or severe symptoms
        elif epds_score > 13 or (mood_score <= 3 and has_crying and has_anxiety):
            risk_level = 'high'
            recommendations.append("📋 Screening indicates HIGH risk for postpartum depression")
            recommendations.append("👩‍⚕️ Schedule doctor appointment within 48 hours")
            recommendations.append("🧠 Postpartum depression is MEDICAL, not weakness - treatment available")
        
        # Medium risk: Moderate symptoms
        elif mood_score <= 5 or epds_score > 9 or (has_crying and sleep_quality == 'poor'):
            risk_level = 'medium'
            recommendations.append("💛 You may be experiencing 'baby blues' or early depression")
            recommendations.append("📞 Discuss with doctor at next checkup (don't wait if worsening)")
        
        # Normal baby blues (80% of mothers, resolves in 2 weeks)
        elif days_postpartum <= 14 and mood_score >= 6:
            recommendations.append("✓ Mood changes are common in first 2 weeks ('baby blues')")
            recommendations.append("⏳ Should improve by week 3. If not, seek help.")
        
        # Supportive care for all
        recommendations.extend([
            "\n🛌 Sleep when baby sleeps (housework can wait)",
            "👨‍👩‍👧 Ask family for help - you don't have to do it alone",
            "🚶‍♀️ Gentle exercise: 10-minute walk with baby improves mood",
            "🗣️ Talk to someone: Friend, mother, ASHA worker, helpline",
            "🍽️ Eat regular meals - nutrition affects mood"
        ])
        
        return {
            'risk_level': risk_level,
            'depression_risk_score': epds_score,
            'immediate_action_needed': immediate_action,
            'recommendations': recommendations,
            'referral_needed': risk_level in ['high', 'critical']
        }
    
    
    async def process_query(
        self,
        query: str,
        mother_context: Dict[str, Any],
        reports_context: List[Dict[str, Any]],
        language: str = 'en'
    ) -> str:
        """
        Process postnatal query with PREGNANCY HISTORY CONTEXT
        
        This method enhances the base agent's process_query by adding
        complete pregnancy history as context for more informed responses.
        """
        if not self.client:
            return (
                "⚠️ Postnatal Care Agent is currently unavailable. "
                "Please try again later or contact support."
            )
        
        try:
            mother_id = mother_context.get('id')
            
            # ✨ NEW: Fetch pregnancy history for context
            logger.info(f"📚 Fetching pregnancy history for mother {mother_id}")
            pregnancy_history = await get_pregnancy_history_context(mother_id)
            history_prompt = format_history_for_prompt(pregnancy_history)
            
            # Build enhanced system prompt with pregnancy history
            system_prompt = self.get_system_prompt()
            
            # Context building
            context_result = await self.build_context(mother_id)
            context_info = context_result.get('context_text', '')
            
            preferred_language = language or mother_context.get('preferred_language', 'en')
            
            # Days postpartum for context
            delivery_date = mother_context.get('delivery_date')
            days_postpartum = "unknown"
            if delivery_date:
                try:
                    from datetime import datetime
                    delivery_dt = datetime.fromisoformat(delivery_date.replace('Z', ''))
                    days_postpartum = (datetime.now() - delivery_dt).days
                except:
                    pass
            
            # Enhanced prompt with pregnancy history
            full_prompt = f"""
CRITICAL: Strictly follow WHO and NHM India guidelines. If High Risk, recommend hospital. Reply ONLY in {preferred_language}.

{system_prompt}

===============================
PREGNANCY HISTORY (MatruRaksha)
===============================
{history_prompt}

IMPORTANT: Use the pregnancy history above as CONTEXT to provide personalized 
postnatal guidance. For example:
- If gestational diabetes → monitor baby's 血sugar and mother's risk
- If anemia during pregnancy → check if iron supplementation still needed
- If high BP/preeclampsia → watch for postpartum hypertension
- If previous complications → consider ongoing monitoring needs

===============================
CURRENT POSTNATAL STATUS
===============================
Days Postpartum: {days_postpartum}
Delivery Type: {mother_context.get('delivery_type', 'unknown')}

{context_info}

===============================
Mother's Question: {query}
===============================

Response:
"""
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            cleaned_response = response.text.strip()
            logger.info(f"✅ Postnatal Agent processed query with pregnancy history context")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ Postnatal Agent error: {e}")
            return (
                f"I apologize, but I encountered an issue processing your request. "
                f"Please try rephrasing your question or contact your healthcare provider if urgent."
            )
    
    def generate_response(
        self, 
        message: str, 
        mother_context: Dict[str, Any],
        postnatal_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual response to postnatal query
        
        Args:
            message: Mother's message/query
            mother_context: Mother's profile data
            postnatal_data: Recent postnatal check-in data
            
        Returns:
            AI-generated response with personalized guidance
        """
        if not GEMINI_AVAILABLE or not self.model:
            return self._fallback_response(message, postnatal_data)
        
        # Build context
        context_parts = [
            f"Mother: {mother_context.get('name', 'Unknown')}",
            f"Days postpartum: {postnatal_data.get('days_postpartum', 'Unknown') if postnatal_data else 'Unknown'}",
            f"Delivery type: {mother_context.get('delivery_type', 'Unknown')}",
            f"Language: {mother_context.get('preferred_language', 'English')}"
        ]
        
        if postnatal_data:
            context_parts.append(f"Recent bleeding status: {postnatal_data.get('bleeding_status', 'Not reported')}")
            context_parts.append(f"Breastfeeding: {postnatal_data.get('breastfeeding_status', 'Not reported')}")
            context_parts.append(f"Mood score (0-10): {postnatal_data.get('mood_score', 'Not reported')}")
        
        full_prompt = f"""Context:
{chr(10).join(context_parts)}

Mother's question: {message}

Provide a warm, evidence-based response following NHM SUMAN postnatal care guidelines. 
Include specific action items if needed."""

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"PostnatalAgent Gemini error: {e}")
            return self._fallback_response(message, postnatal_data)
    
    def _fallback_response(self, message: str, postnatal_data: Optional[Dict[str, Any]] = None) -> str:
        """Fallback response when Gemini is unavailable"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['bleeding', 'blood', 'lochia']):
            return """Normal postpartum bleeding (lochia):
- Days 1-3: Red, moderate flow
- Days 4-10: Pink/brown, lighter
- Week 2-6: Yellowish, minimal

⚠️ SEE DOCTOR IF:
- Soaking >1 pad/hour for 2+ hours
- Large clots (>golf ball)
- Foul smell
- Fever

Stay hydrated, rest, avoid heavy lifting."""

        elif any(word in message_lower for word in ['breastfeed', 'feeding', 'milk', 'nipple']):
            return """Breastfeeding tips:
🤱 Feed 8-12 times/day
✓ Check latch: Baby's mouth covers areola
💧 Drink 3-4L water daily
🌾 Eat nutritious food

For sore nipples:
- Apply breast milk after feeding
- Check baby's latch
- Try different positions

📞 Contact ASHA worker for hands-on support"""

        elif any(word in message_lower for word in ['sad', 'cry', 'depressed', 'anxiety', 'sleep']):
            return """It's common to feel overwhelmed after childbirth.

Normal 'baby blues' (80% of mothers):
- Mood swings, crying
- Should improve in 2 weeks

⚠️ SEEK HELP IF:
- Lasting >2 weeks
- Can't care for baby
- Thoughts of harm

🆘 Helpline: 08046110007

💛 You're not alone. Treatment available."""

        else:
            return """I'm here to help with postnatal recovery questions!

Common topics:
- Bleeding and physical recovery
- Breastfeeding support
- Cesarean care
- Mental health
- When to see doctor

What specific concern can I help you with?"""
