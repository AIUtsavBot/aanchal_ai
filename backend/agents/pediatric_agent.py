"""
SantanRaksha - Pediatric Care Agent
Handles general child health queries for children 0-5 years

Aligned with:
- IMNCI (Integrated Management of Neonatal and Childhood Illness)
- IAP (Indian Academy of Pediatrics) Guidelines
- WHO Child Health Standards
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PediatricAgent(BaseAgent):
    """
    Specialized agent for pediatric care and child health
    
    Handles:
    - Common childhood illnesses (fever, cough, diarrhea)
    - IMNCI danger signs recognition
    - Feeding guidance (complementary feeding)
    - Sleep and development questions
    - When to seek medical care
    """
    
    
    def __init__(self):
        super().__init__(
            agent_name="Pediatric Agent",
            agent_role="Pediatric Care Specialist"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a specialized Pediatric Care Expert for the SantanRaksha child health system.

Your role: Provide evidence-based guidance for parents caring for children 0-5 years using IMNCI (Integrated Management of Neonatal and Childhood Illness) protocols.

IMNCI DANGER SIGNS - IMMEDIATE HOSPITAL REFERRAL:

NEWBORNS (0-2 months):
1. Unable to feed/drink
2. Convulsions
3. Drowsy/unconscious
4. Movement only when stimulated or no movement
5. Fast breathing (≥60/min)
6. Severe chest indrawing
7. Grunting
8. Temperature <35.5°C or ≥37.5°C
9. Umbilical cord red or draining pus

INFANTS & CHILDREN (2 months - 5 years):
1. Unable to drink or breastfeed
2. Vomits everything
3. Convulsions
4. Lethargic or unconscious
5. Stridor when calm (high-pitched breathing sound)
6. Severe malnutrition (visible severe wasting)

FEVER MANAGEMENT:
- <3 months: ANY fever = doctor visit
- 3-6 months: Fever >101°F (38.3°C) = doctor visit
- >6 months: Fever >103°F (39.4°C) or lasting >3 days = doctor visit
- RED FLAGS: Fever + rash, stiff neck, difficulty breathing, extreme fussiness

Fever treatment:
✓ Paracetamol (Calpol): 10-15 mg/kg every 4-6 hours
✓ Lukewarm sponging (NOT cold water)
✓ Light clothing, room ventilation
✗ NEVER: Aspirin, ice baths, alcohol rubs

DIARRHEA MANAGEMENT (IMNCI):
- Mild: 50-100ml ORS after each loose stool
- Moderate: ORS 75ml/kg over 4 hours + zinc
- Severe: IV fluids at hospital

Zinc supplementation:
- <6 months: 10mg daily for 14 days
- >6 months: 20mg daily for 14 days

Danger signs:
⚠️ Sunken eyes, no tears, dry mouth
⚠️ Lethargy, drinks poorly
⚠️ Blood in stool
⚠️ High fever with diarrhea

RESPIRATORY INFECTIONS:
Pneumonia signs:
- Fast breathing: <2 months ≥60/min, 2-12 months ≥50/min, 1-5 years ≥40/min
- Chest indrawing
- Nasal flaring
- Grunting

Mild cough/cold:
✓ Continue breastfeeding
✓ Clear nose with saline drops
✓ Honey for >1 year (cough relief)
✗ NO cough syrups for <2 years
✗ NO decongestants

FEEDING GUIDELINES (WHO IYCF):
0-6 months: EXCLUSIVE breastfeeding
6-8 months: Breast milk + 2-3 complementary feeds
9-11 months: Breast milk + 3-4 complementary feeds + snacks
12-24 months: Family foods + continued breastfeeding

Complementary feeding start (6 months):
- Signs of readiness: Sits with support, shows interest in food, loss of tongue-thrust reflex
- First foods: Mashed banana, rice cereal, dal water, mashed potato
- Iron-rich: Introduce early (fortified cereals, green leafy vegetables, jaggery)
- Allergens: Introduce one at a time (egg, fish, peanuts) - observe 3 days

Minimum Dietary Diversity (>6 months): 4+ food groups daily
1. Grains (rice, wheat, ragi)
2. Legumes (dal, rajma)
3. Dairy (milk, curd, paneer)
4. Eggs/Meat/Fish
5. Fruits (mashed/pureed)
6. Vegetables (cooked)

SLEEP GUIDELINES (AAP):
- Newborn: 14-17 hours/day
- 4-12 months: 12-16 hours/day (including naps)
- 1-2 years: 11-14 hours/day
- 3-5 years: 10-13 hours/day

Safe sleep:
✓ Back to sleep
✓ Firm mattress, no pillows/toys
✗ Co-sleeping (SIDS risk)

RESPONSE FORMAT:
1. Assess severity using IMNCI danger signs
2. Provide immediate guidance (home care vs. doctor visit)
3. Educate on what's normal vs. concerning
4. Offer practical tips
5. Escalate if danger signs present

Always respond in the parent's preferred language (Hindi/Marathi/English).
Use simple, actionable language.
Empower parents while ensuring child safety."""
    
    
    async def assess_fever_risk(self, fever_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess fever severity using IMNCI guidelines
        
        Args:
            fever_data: Dict with temperature, age_months, duration_days, symptoms
            
        Returns:
            Risk assessment with recommendations
        """
        temp_celsius = fever_data.get('temperature_celsius', 0)
        age_months = fever_data.get('age_months', 0)
        duration_days = fever_data.get('duration_days', 0)
        symptoms = fever_data.get('symptoms', [])
        
        risk_level = 'low'
        recommendations = []
        seek_immediate_care = False
        
        # Critical: Any fever in newborns
        if age_months < 3:
            risk_level = 'critical'
            seek_immediate_care = True
            recommendations.append("🚨 URGENT: Any fever in babies <3 months requires immediate doctor visit")
            recommendations.append("📞 Call pediatrician NOW or go to nearest hospital")
        
        # High risk: Young infant with high fever
        elif age_months < 6 and temp_celsius >= 38.3:
            risk_level = 'high'
            seek_immediate_care = True
            recommendations.append("⚠️ HIGH FEVER in young infant. Doctor visit needed TODAY")
        
        # High risk: Very high fever or prolonged
        elif temp_celsius >= 39.4 or duration_days >= 3:
            risk_level = 'high'
            recommendations.append("⚠️ High/prolonged fever. Schedule doctor visit within 24 hours")
        
        # High risk: Danger symptoms present
        danger_symptoms = ['rash', 'stiff_neck', 'difficulty_breathing', 'convulsions', 
                          'lethargic', 'not_drinking', 'severe_headache']
        if any(s in symptoms for s in danger_symptoms):
            risk_level = 'critical'
            seek_immediate_care = True
            recommendations.append("🚨 DANGER SIGN detected. Go to hospital IMMEDIATELY")
        
        # Moderate fever - home management
        elif temp_celsius >= 38.0:
            risk_level = 'medium'
            recommendations.extend([
                f"💊 Paracetamol dose: {self._calculate_paracetamol_dose(fever_data.get('weight_kg', 0))} ml every 4-6 hours",
                "🌡️ Lukewarm sponging (NOT cold water)",
                "👕 Dress in light, breathable clothing",
                "💧 Give plenty of fluids (breast milk/water)",
                "🏠 Monitor every 2-3 hours"
            ])
            recommendations.append("⏰ If fever persists >24 hours or worsens, contact doctor")
        
        # Low-grade fever
        else:
            recommendations.extend([
                "✓ Low-grade fever - body fighting infection",
                "💧 Keep child well-hydrated",
                "🛌 Adequate rest",
                "📊 Monitor temperature every 4 hours"
            ])
        
        return {
            'risk_level': risk_level,
            'seek_immediate_care': seek_immediate_care,
            'recommendations': recommendations,
            'assessment_summary': f"Fever {temp_celsius}°C in {age_months}-month-old: {risk_level} risk"
        }
    
    async def assess_diarrhea_dehydration(self, diarrhea_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess diarrhea and dehydration using IMNCI classification
        
        Args:
            diarrhea_data: Dict with frequency, duration, dehydration_signs
            
        Returns:
            Dehydration assessment with ORS guidance
        """
        frequency_per_day = diarrhea_data.get('frequency_per_day', 0)
        duration_days = diarrhea_data.get('duration_days', 0)
        has_blood = diarrhea_data.get('has_blood_in_stool', False)
        dehydration_signs = diarrhea_data.get('dehydration_signs', [])
        age_months = diarrhea_data.get('age_months', 0)
        weight_kg = diarrhea_data.get('weight_kg', 0)
        
        risk_level = 'low'
        recommendations = []
        ors_plan = 'A'  # A=No dehydration, B=Some dehydration, C=Severe dehydration
        
        # Severe dehydration (IMNCI: 2+ signs)
        severe_signs = ['lethargic', 'sunken_eyes', 'very_slow_skin_pinch', 'unable_to_drink']
        severe_count = sum(1 for sign in severe_signs if sign in dehydration_signs)
        
        if severe_count >= 2:
            risk_level = 'critical'
            ors_plan = 'C'
            recommendations.append("🚨 SEVERE DEHYDRATION - HOSPITAL IMMEDIATELY (IV fluids needed)")
            recommendations.append("📞 Call 108 ambulance if unable to transport")
        
        # Some dehydration (IMNCI: 2+ signs)
        some_signs = ['restless', 'sunken_eyes', 'thirsty', 'slow_skin_pinch']
        some_count = sum(1 for sign in some_signs if sign in dehydration_signs)
        
        if some_count >= 2 or frequency_per_day >= 8:
            risk_level = 'medium'
            ors_plan = 'B'
            ors_ml_needed = weight_kg * 75  # WHO Plan B: 75ml/kg over 4 hours
            recommendations.append(f"⚠️ MODERATE DEHYDRATION - ORS Plan B")
            recommendations.append(f"💧 Give {ors_ml_needed}ml ORS over next 4 hours (small sips every 5 min)")
            recommendations.append(f"🥄 After 4 hours, switch to Plan A maintenance")
            recommendations.append("🏥 If child vomits, or can't drink - go to doctor")
        
        # Dysentery (blood in stool)
        elif has_blood:
            risk_level = 'high'
            recommendations.append("⚠️ BLOOD IN STOOL - Doctor visit needed for antibiotics")
            recommendations.append("💧 Continue ORS to prevent dehydration")
        
        # No dehydration - home management
        else:
            risk_level = 'low'
            recommendations.extend([
                "✓ NO severe dehydration - Manage at home with ORS",
                "💧 ORS Plan A: 50-100ml after each loose stool",
                "🍼 Continue breastfeeding (MORE frequent if infant)",
                "🍚 Continue normal foods (banana, rice, curd, khichdi)",
                f"⚡ Zinc: {self._get_zinc_dose(age_months)} daily for 14 days (prevents future episodes)"
            ])
        
        # General advice
        recommendations.append("\n📋 DANGER SIGNS - Go to hospital if:")
        recommendations.append("   • Can't drink or vomiting everything")
        recommendations.append("   • Very sleepy/lethargic")
        recommendations.append("   • Blood in stool")
        recommendations.append("   • No improvement in 24 hours")
        
        return {
            'risk_level': risk_level,
            'dehydration_level': ors_plan,
            'ors_plan': ors_plan,
            'recommendations': recommendations,
            'refer_to_hospital': ors_plan == 'C' or has_blood
        }
    
    async def assess_respiratory_symptoms(self, resp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess respiratory symptoms for pneumonia using IMNCI criteria
        
        Args:
            resp_data: Dict with respiratory_rate, chest_indrawing, cough_duration
            
        Returns:
            Pneumonia risk assessment
        """
        resp_rate = resp_data.get('respiratory_rate', 0)
        age_months = resp_data.get('age_months', 0)
        has_chest_indrawing = resp_data.get('chest_indrawing', False)
        has_nasal_flaring = resp_data.get('nasal_flaring', False)
        has_grunting = resp_data.get('grunting', False)
        has_stridor = resp_data.get('stridor', False)
        cough_duration_days = resp_data.get('cough_duration_days', 0)
        
        # IMNCI fast breathing thresholds
        if age_months < 2:
            fast_breathing_threshold = 60
        elif age_months < 12:
            fast_breathing_threshold = 50
        else:
            fast_breathing_threshold = 40
        
        is_fast_breathing = resp_rate >= fast_breathing_threshold
        
        risk_level = 'low'
        recommendations = []
        urgent_referral = False
        
        # Severe pneumonia (IMNCI)
        if has_chest_indrawing or has_grunting or has_stridor or has_nasal_flaring:
            risk_level = 'critical'
            urgent_referral = True
            recommendations.append("🚨 SEVERE PNEUMONIA SIGNS - Hospital IMMEDIATELY")
            recommendations.append("⚠️ Child needs oxygen and antibiotics")
            recommendations.append("🚑 Call 108 if no transport available")
        
        # Pneumonia (IMNCI: Fast breathing alone)
        elif is_fast_breathing:
            risk_level = 'high'
            recommendations.append(f"⚠️ FAST BREATHING detected ({resp_rate}/min, normal <{fast_breathing_threshold})")
            recommendations.append("🏥 Doctor visit needed TODAY for antibiotics")
            recommendations.append("💊 Likely needs Amoxicillin treatment")
        
        # Prolonged cough
        elif cough_duration_days >= 14:
            risk_level = 'medium'
            recommendations.append("⚠️ Cough lasting >2 weeks - Doctor checkup needed")
            recommendations.append("🔍 Rule out: Tuberculosis, asthma, whooping cough")
        
        # Simple cough/cold
        else:
            risk_level = 'low'
            recommendations.extend([
                "✓ Simple cough/cold - Home care supportive",
                "🍼 Continue breastfeeding (boosts immunity)",
                "💧 Clear nose with saline drops before feeding",
                "🍯 Honey (if >1 year): 1/2 tsp for cough relief",
                "💨 Keep room well-ventilated",
                "🚫 NO cough syrups for children <2 years (not effective)",
                "⏰ See doctor if: Breathing difficulty, fever >3 days, not eating/drinking"
            ])
        
        return {
            'risk_level': risk_level,
            'pneumonia_suspected': is_fast_breathing or has_chest_indrawing,
            'urgent_referral_needed': urgent_referral,
            'recommendations': recommendations
        }
    
    def _calculate_paracetamol_dose(self, weight_kg: float) -> str:
        """Calculate paracetamol dose (mg) based on weight"""
        if weight_kg == 0:
            return "Consult doctor for exact dose"
        
        # 10-15 mg/kg, using Calpol 120mg/5ml (most common in India)
        mg_per_kg = 15  # Maximum safe dose
        dose_mg = weight_kg * mg_per_kg
        dose_ml = (dose_mg / 120) * 5  # Convert to Calpol 120mg/5ml
        
        return f"{dose_ml:.1f}"
    
    def _get_zinc_dose(self, age_months: int) -> str:
        """Get zinc dose per WHO guidelines"""
        if age_months < 6:
            return "10mg (1/2 tablet)"
        else:
            return "20mg (1 tablet)"
    
    def generate_response(
        self, 
        message: str, 
        child_context: Dict[str, Any],
        health_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual response to pediatric query
        
        Args:
            message: Parent's message/query
            child_context: Child's profile data
            health_data: Recent health timeline data
            
        Returns:
            AI-generated response with personalized guidance
        """
        if not GEMINI_AVAILABLE or not self.model:
            return self._fallback_response(message)
        
        # Build context
        age_months = child_context.get('age_months', 0)
        context_parts = [
            f"Child: {child_context.get('name', 'Unknown')}",
            f"Age: {age_months} months ({age_months // 12}y {age_months % 12}m)",
            f"Weight: {child_context.get('weight_kg', 'Unknown')} kg",
            f"Language: {child_context.get('preferred_language', 'English')}"
        ]
        
        if health_data:
            context_parts.append(f"Recent health issue: {health_data.get('recent_illness', 'None reported')}")
        
        full_prompt = f"""Context:
{chr(10).join(context_parts)}

Parent's question: {message}

Provide evidence-based guidance following IMNCI protocols.
Include IMNCI danger signs if relevant.
Be specific about when to see a doctor."""

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"PediatricAgent Gemini error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when Gemini is unavailable"""
        return """I'm here to help with child health questions!

Common concerns:
🌡️ **Fever**: Paracetamol dose, when to worry
💧 **Diarrhea**: ORS, dehydration signs
😷 **Cough/Cold**: Home care, danger signs
🍼 **Feeding**: Complementary feeding, nutrition
😴 **Sleep**: Safe sleep, schedules

🚨 SEEK IMMEDIATE CARE IF:
- Difficulty breathing
- Unable to drink
- Extreme lethargy
- Convulsions
- High fever in baby <3 months

What specific concern can I help with?"""
