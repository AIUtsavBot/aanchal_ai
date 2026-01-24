"""
SantanRaksha - Vaccination Agent
Handles vaccination schedule, reminders, and queries

Aligned with:
- IAP (Indian Academy of Pediatrics) Immunization Schedule 2023
- Universal Immunization Programme (UIP)
- WHO Vaccine Safety Monitoring
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

logger = logging.getLogger(__name__)


class VaccineAgent(BaseAgent):
    """
    Specialized agent for vaccination management
    
    Handles:
    - IAP 2023 immunization schedule
    - Vaccine reminders and tracking
    - Side effect management
    - Catch-up schedules for delayed vaccines
    - Vaccine education and myth-busting
    """
    
    # IAP 2023 Comprehensive Immunization Schedule
    IAP_SCHEDULE = {
        'birth': [
            {'name': 'BCG', 'age_days': 0, 'description': 'Tuberculosis protection'},
            {'name': 'OPV-0', 'age_days': 0, 'description': 'Polio (birth dose)'},
            {'name': 'Hepatitis B-1', 'age_days': 0, 'description': 'Hepatitis B (birth dose)'},
        ],
        '6_weeks': [
            {'name': 'OPV-1', 'age_days': 42, 'description': 'Polio dose 1'},
            {'name': 'Pentavalent-1', 'age_days': 42, 'description': 'DPT+Hep B+Hib'},
            {'name': 'Rotavirus-1', 'age_days': 42, 'description': 'Diarrhea prevention'},
            {'name': 'PCV-1', 'age_days': 42, 'description': 'Pneumonia prevention'},
            {'name': 'IPV-1', 'age_days': 42, 'description': 'Injectable polio'},
        ],
        '10_weeks': [
            {'name': 'OPV-2', 'age_days': 70, 'description': 'Polio dose 2'},
            {'name': 'Pentavalent-2', 'age_days': 70, 'description': 'DPT+Hep B+Hib dose 2'},
            {'name': 'Rotavirus-2', 'age_days': 70, 'description': 'Diarrhea prevention dose 2'},
            {'name': 'PCV-2', 'age_days': 70, 'description': 'Pneumonia prevention dose 2'},
        ],
        '14_weeks': [
            {'name': 'OPV-3', 'age_days': 98, 'description': 'Polio dose 3'},
            {'name': 'Pentavalent-3', 'age_days': 98, 'description': 'DPT+Hep B+Hib dose 3'},
            {'name': 'Rotavirus-3', 'age_days': 98, 'description': 'Diarrhea prevention dose 3'},
            {'name': 'PCV-3', 'age_days': 98, 'description': 'Pneumonia prevention dose 3'},
            {'name': 'IPV-2', 'age_days': 98, 'description': 'Injectable polio dose 2'},
        ],
        '6_months': [
            {'name': 'Influenza-1', 'age_days': 180, 'description': 'Flu vaccine (optional)', 'optional': True},
        ],
        '7_months': [
            {'name': 'Influenza-2', 'age_days': 210, 'description': 'Flu vaccine dose 2 (optional)', 'optional': True},
        ],
        '9_months': [
            {'name': 'MR-1', 'age_days': 270, 'description': 'Measles-Rubella dose 1'},
            {'name': 'JE-1', 'age_days': 270, 'description': 'Japanese Encephalitis dose 1'},
            {'name': 'Vitamin A', 'age_days': 270, 'description': 'Vitamin A supplementation'},
        ],
        '12_months': [
            {'name': 'Hepatitis A-1', 'age_days': 365, 'description': 'Hepatitis A (optional)', 'optional': True},
            {'name': 'Typhoid Conjugate Vaccine', 'age_days': 365, 'description': 'Typhoid protection'},
        ],
        '15_months': [
            {'name': 'MMR-1', 'age_days': 450, 'description': 'Measles-Mumps-Rubella (optional)', 'optional': True},
            {'name': 'Varicella-1', 'age_days': 450, 'description': 'Chickenpox (optional)', 'optional': True},
            {'name': 'PCV Booster', 'age_days': 450, 'description': 'Pneumonia booster'},
        ],
        '16-18_months': [
            {'name': 'Pentavalent Booster', 'age_days': 510, 'description': 'DPT+Hep B+Hib booster'},
            {'name': 'OPV Booster', 'age_days': 510, 'description': 'Polio booster'},
            {'name': 'MR-2', 'age_days': 510, 'description': 'Measles-Rubella dose 2'},
            {'name': 'JE-2', 'age_days': 510, 'description': 'Japanese Encephalitis dose 2'},
        ],
        '18_months': [
            {'name': 'Hepatitis A-2', 'age_days': 540, 'description': 'Hepatitis A dose 2 (optional)', 'optional': True},
        ],
        '2_years': [
            {'name': 'Typhoid Booster', 'age_days': 730, 'description': 'Typhoid booster (every 3 years)'},
        ],
        '4-6_years': [
            {'name': 'DPT Booster 2', 'age_days': 1460, 'description': 'DPT booster dose 2'},
            {'name': 'OPV Booster 2', 'age_days': 1460, 'description': 'Polio booster dose 2'},
            {'name': 'MMR-2', 'age_days': 1460, 'description': 'MMR dose 2 (optional)', 'optional': True},
            {'name': 'Varicella-2', 'age_days': 1460, 'description': 'Chickenpox dose 2 (optional)', 'optional': True},
        ],
    }
    
    
    def __init__(self):
        super().__init__(
            agent_name="Vaccine Agent",
            agent_role="Vaccination Specialist"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a specialized Vaccination Expert for the SantanRaksha child health system.

Your role: Provide accurate, evidence-based information about childhood vaccinations following IAP 2023 guidelines.

KEY RESPONSIBILITIES:
1. Educate parents about vaccine importance
2. Explain common side effects and management
3. Address vaccine hesitancy with empathy and facts
4. Identify contraindications
5. Coordinate catch-up schedules for delayed vaccines

COMMON VACCINE SIDE EFFECTS (NORMAL):
- Mild fever (<101°F): Give paracetamol, plenty of fluids
- Injection site redness/swelling: Cold compress
- Fussiness/crying: Comfort, feeds
- Loss of appetite (1-2 days): Normal
- Duration: Usually resolve in 24-48 hours

SERIOUS SIDE EFFECTS (RARE - SEEK IMMEDIATE CARE):
- High fever >103°F (39.4°C)
- Severe allergic reaction (anaphylaxis): Difficulty breathing, hives, swelling
- Prolonged crying >3 hours
- Seizures
- Extreme lethargy

Note: Serious reactions are EXTREMELY RARE (1 in 100,000-1 million doses)

CONTRAINDICATIONS:
Temporary delay if:
- Moderate/severe illness with fever
- Recent blood transfusion (for live vaccines)
- Immunosuppressant therapy

Absolute contraindications:
- Severe allergic reaction to previous dose
- Severe immunodeficiency (for live vaccines)

MYTH-BUSTING:
❌ MYTH: "Vaccines cause autism"
✓ FACT: Extensively studied, NO link found. Autism is genetic/developmental.

❌ MYTH: "Too many vaccines overwhelm immune system"
✓ FACT: Infant immune system can handle thousands of antigens. Vaccines use <200.

❌ MYTH: "Natural immunity is better"
✓ FACT: Diseases carry serious risks (death, disability). Vaccines provide safe immunity.

❌ MYTH: "Vaccines contain harmful chemicals"
✓ FACT: Ingredients are in trace amounts, rigorously tested for safety.

❌ MYTH: "Polio is eradicated, no need for vaccine"
✓ FACT: India polio-free since 2014, but risk of re-importation exists. Continue vaccination.

CATCH-UP SCHEDULE:
- Delays <4 weeks: Resume as scheduled
- Delays >4 weeks: Accelerated schedule possible
- NO need to restart series
- Prioritize: BCG (if not given), DPT, Polio, Measles

RESPONSE FORMAT:
1. Acknowledge parent's concern
2. Provide scientific facts (but in simple language)
3. Address fears with empathy
4. Give practical guidance (next vaccine, side effect management)
5. Encourage adherence to schedule

Always respond in the parent's preferred language (Hindi/Marathi/English).
Be patient, non-judgmental, and supportive."""
    
    
    async def get_next_vaccines(self, child_data: Dict[str, Any], vaccination_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get next due vaccines for a child
        
        Args:
            child_data: Dict with birth_date, age_months
            vaccination_records: List of vaccination records
            
        Returns:
            List of next 3-5 due vaccines with dates
        """
        birth_date = child_data.get('birth_date')
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        
        # Get all pending/overdue vaccines
        pending_vaccines = [
            v for v in vaccination_records 
            if v.get('status') in ['pending', 'overdue']
        ]
        
        # Sort by due date
        pending_vaccines.sort(key=lambda x: x.get('due_date', ''))
        
        next_vaccines = []
        for vaccine in pending_vaccines[:5]:  # Return next 5
            due_date = vaccine.get('due_date')
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            days_until_due = (due_date - datetime.now().date()).days
            
            next_vaccines.append({
                'vaccine_name': vaccine.get('vaccine_name'),
                'due_date': due_date.strftime('%d %b %Y'),
                'days_until_due': days_until_due,
                'status': 'overdue' if days_until_due < 0 else 'upcoming',
                'description': self._get_vaccine_description(vaccine.get('vaccine_name'))
            })
        
        return {
            'next_vaccines': next_vaccines,
            'overdue_count': sum(1 for v in next_vaccines if v['status'] == 'overdue'),
            'urgent_attention_needed': any(v['days_until_due'] < -30 for v in next_vaccines)
        }
    
    async def assess_side_effects(self, side_effect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess vaccine side effects and provide guidance
        
        Args:
            side_effect_data: Dict with symptoms, severity, hours_since_vaccination
            
        Returns:
            Assessment and management recommendations
        """
        symptoms = side_effect_data.get('symptoms', [])
        hours_since = side_effect_data.get('hours_since_vaccination', 0)
        fever_temp = side_effect_data.get('fever_temperature_celsius', 0)
        vaccine_name = side_effect_data.get('vaccine_name', '')
        
        risk_level = 'low'
        recommendations = []
        seek_immediate_care = False
        
        # Serious reactions - immediate care
        serious_symptoms = ['difficulty_breathing', 'severe_allergic_reaction', 'seizure', 
                           'extreme_lethargy', 'prolonged_crying_3hours']
        
        if any(s in symptoms for s in serious_symptoms):
            risk_level = 'critical'
            seek_immediate_care = True
            recommendations.append("🚨 SERIOUS REACTION - GO TO HOSPITAL IMMEDIATELY")
            recommendations.append("📞 Call 108 ambulance if needed")
            return {
                'risk_level': risk_level,
                'seek_immediate_care': seek_immediate_care,
                'recommendations': recommendations
            }
        
        # High fever
        if fever_temp >= 39.4:  # >103°F
            risk_level = 'medium'
            recommendations.append("⚠️ High fever post-vaccination")
            recommendations.append(f"💊 Give paracetamol: 10-15mg/kg every 4-6 hours")
            recommendations.append("🧊 Lukewarm sponging")
            recommendations.append("📞 If fever persists >24 hours or worsens, contact doctor")
        
        # Normal mild reactions
        else:
            risk_level = 'low'
            
            if 'fever' in symptoms or fever_temp > 37.5:
                recommendations.extend([
                    "✓ Mild fever is NORMAL after vaccination (immune system working)",
                    "💊 Paracetamol if uncomfortable",
                    "💧 Give plenty of fluids",
                    "⏰ Should resolve in 24-48 hours"
                ])
            
            if 'injection_site_pain' in symptoms or 'redness' in symptoms or 'swelling' in symptoms:
                recommendations.extend([
                    "✓ Injection site reactions are VERY COMMON",
                    "🧊 Cold compress for 10-15 minutes",
                    "🚫 Don't rub or massage the area",
                    "⏰ Should improve in 2-3 days"
                ])
            
            if 'fussiness' in symptoms or 'crying' in symptoms:
                recommendations.extend([
                    "✓ Fussiness is normal for 24-48 hours",
                    "🤱 Extra cuddles and comfort",
                    "🍼 Frequent breastfeeding (helps soothe)"
                ])
            
            if 'loss_of_appetite' in symptoms:
                recommendations.append("✓ Reduced appetite for 1-2 days is normal, should return")
        
        # General reassurance
        if risk_level == 'low':
            recommendations.append("\n💚 These reactions show the vaccine is working!")
            recommendations.append("🛡️ Your baby is building immunity to serious diseases")
        
        # Vaccine-specific guidance
        if 'BCG' in vaccine_name:
            recommendations.append("\nℹ️ BCG NOTE: Small bump/scab at site is NORMAL, heals in 4-6 weeks")
        
        return {
            'risk_level': risk_level,
            'seek_immediate_care': seek_immediate_care,
            'is_normal_reaction': risk_level == 'low',
            'recommendations': recommendations,
            'expected_duration_hours': 48 if risk_level == 'low' else None
        }
    
    def _get_vaccine_description(self, vaccine_name: str) -> str:
        """Get description for a vaccine"""
        descriptions = {
            'BCG': 'Protects against severe tuberculosis (TB)',
            'OPV': 'Oral polio vaccine - prevents polio paralysis',
            'Pentavalent': 'Combo vaccine: DPT + Hepatitis B + Hib (5-in-1 protection)',
            'Rotavirus': 'Prevents severe diarrhea and dehydration',
            'PCV': 'Pneumococcal vaccine - prevents pneumonia and meningitis',
            'IPV': 'Injectable polio vaccine',
            'MR': 'Measles-Rubella - prevents serious rash diseases',
            'JE': 'Japanese Encephalitis - brain infection prevention',
            'Hepatitis A': 'Prevents liver disease',
            'Typhoid': 'Prevents typhoid fever',
            'MMR': 'Measles-Mumps-Rubella (3-in-1)',
            'Varicella': 'Chickenpox vaccine',
            'DPT': 'Diphtheria-Pertussis-Tetanus',
            'Influenza': 'Seasonal flu vaccine',
        }
        
        for key in descriptions:
            if key in vaccine_name:
                return descriptions[key]
        
        return 'Protects against serious disease'
    
    def generate_response(
        self, 
        message: str, 
        child_context: Dict[str, Any],
        vaccination_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual response to vaccination query
        
        Args:
            message: Parent's message/query
            child_context: Child's profile data
            vaccination_data: Recent vaccination records
            
        Returns:
            AI-generated response with personalized guidance
        """
        if not GEMINI_AVAILABLE or not self.model:
            return self._fallback_response(message)
        
        # Build context
        context_parts = [
            f"Child: {child_context.get('name', 'Unknown')}",
            f"Age: {child_context.get('age_months', 'Unknown')} months",
            f"Language: {child_context.get('preferred_language', 'English')}"
        ]
        
        if vaccination_data:
            next_vaccine = vaccination_data.get('next_vaccine', 'Unknown')
            context_parts.append(f"Next vaccine due: {next_vaccine}")
        
        full_prompt = f"""Context:
{chr(10).join(context_parts)}

Parent's question: {message}

Provide evidence-based guidance following IAP 2023 immunization schedule.
Address vaccine hesitancy with empathy and facts.
Explain benefits clearly."""

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"VaccineAgent Gemini error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response when Gemini is unavailable"""
        message_lower = message.lower()
        
        if 'side effect' in message_lower or 'fever after' in message_lower:
            return """Common vaccine side effects (NORMAL):
💉 Injection site pain/redness
🌡️ Mild fever (<101°F)
😢 Fussiness for 24-48 hours
🍼 Reduced appetite (1-2 days)

Treatment:
💊 Paracetamol for fever/pain
🧊 Cold compress on injection site
🤱 Extra cuddles and breastfeeding

🚨 SEEK CARE IF:
- High fever >103°F
- Difficulty breathing
- Severe allergic reaction
- Prolonged crying >3 hours

These reactions show immunity is building! 💪"""

        elif 'safe' in message_lower or 'autism' in message_lower or 'harmful' in message_lower:
            return """Vaccines are RIGOROUSLY tested and SAFE:

✅ Millions of doses given safely worldwide
✅ Continuous monitoring for safety
✅ Benefits FAR outweigh tiny risks

MYTH vs FACT:
❌ Vaccines cause autism → ✓ NO link (30+ studies)
❌ Too many vaccines → ✓ Immune system can handle
❌ Natural immunity better → ✓ Diseases carry serious risks

🛡️ Vaccines prevent:
- Death
- Disability
- Hospitalization
- Disease spread

💚 Protecting your child IS loving your child!"""

        else:
            return """I'm your vaccination guide!

I can help with:
📅 **Vaccine schedule** - What's due next?
💉 **Side effects** - Is this normal?
❓ **Vaccine safety** - Addressing concerns
⏰ **Catch-up plans** - Missed vaccines?
🏥 **Where to vaccinate** - Nearest center

💡 TIP: Vaccines are FREE at government health centers!

What specifically would you like to know?"""
