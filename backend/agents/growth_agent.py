"""
SantanRaksha - Growth Monitoring Agent
Handles child growth tracking and nutritional assessment

Aligned with:
- WHO Child Growth Standards (2006)
- RBSK (Rashtriya Bal Swasthya Karyakram) screening
- IAP Growth Monitoring Guidelines
- NIN (National Institute of Nutrition) recommendations
"""

import os
import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GrowthAgent(BaseAgent):
    """
    Specialized agent for growth monitoring and nutrition
    
    Handles:
    - WHO z-score calculation and interpretation
    - Growth faltering detection
    - Malnutrition screening (RBSK 4Ds)
    - Feeding recommendations (IYCF guidelines)
    - Growth chart generation
    """
    
    
    def __init__(self):
        super().__init__(
            agent_name="Growth Agent",
            agent_role="Growth Monitoring & Nutrition Specialist"
        )
    
    def get_system_prompt(self) -> str:
        return """You are a specialized Growth Monitoring & Nutrition Expert for the SantanRaksha child health system.

Your role: Monitor child growth using WHO standards and provide nutrition guidance following WHO IYCF (Infant and Young Child Feeding) recommendations.

WHO GROWTH STANDARDS - Z-SCORE INTERPRETATION:

Z-scores compare child's growth to WHO reference population:
- Z-score = (Observed value - Median) / Standard Deviation

WEIGHT-FOR-AGE (Underweight):
• +2 to -2 SD: NORMAL (85% of children)
• -2 to -3 SD: MODERATE UNDERWEIGHT (flag for monitoring)
• < -3 SD: SEVERE UNDERWEIGHT (urgent intervention)

HEIGHT-FOR-AGE (Stunting - chronic malnutrition):
• +2 to -2 SD: NORMAL
• -2 to -3 SD: MODERATE STUNTING (long-term nutritional deficiency)
• < -3 SD: SEVERE STUNTING (urgent intervention + developmental delays)

WEIGHT-FOR-HEIGHT (Wasting - acute malnutrition):
• +2 to -2 SD: NORMAL
• -2 to -3 SD: MODERATE ACUTE MALNUTRITION (MAM) - RUTF + close monitoring
• < -3 SD: SEVERE ACUTE MALNUTRITION (SAM) - hospitalization may be needed
• > +2 SD: OVERWEIGHT (risk of childhood obesity)
• > +3 SD: OBESE (intervention needed)

MID-UPPER ARM CIRCUMFERENCE (MUAC) - Quick malnutrition screening:
• ≥12.5 cm: NORMAL
• 11.5-12.5 cm: MODERATE malnutrition
• <11.5 cm: SEVERE malnutrition (emergency)

RBSK 4Ds SCREENING (Rashtriya Bal Swasthya Karyakram):
1. **Defects at birth**: Cleft lip, club foot, heart defects
2. **Deficiencies**: Anemia, vitamin deficiencies, malnutrition
3. **Diseases**: Childhood illnesses, infections
4. **Developmental delays**: Motor, cognitive, language delays

GROWTH FALTERING INDICATORS:
⚠️ RED FLAGS:
- Weight loss in consecutive measurements
- Crossing >2 percentile lines downward
- Height plateau for >3 months
- MUAC <11.5 cm
- No weight gain for 2 consecutive months

WHO INFANT AND YOUNG CHILD FEEDING (IYCF) GUIDELINES:

BIRTH - 6 MONTHS:
✓ EXCLUSIVE BREASTFEEDING (NO water, formula, or foods)
✓ On-demand feeding (8-12 times/day)
✓ Colostrum is "liquid gold" - first feed within 1 hour of birth

6-8 MONTHS - Complementary Feeding Introduction:
✓ Continue breastfeeding
✓ Start with 2-3 meals/day
✓ Consistency: Thick porridge, mashed foods
✓ Amount: 2-3 tablespoons, gradually increase

First foods (iron-rich):
- Fortified rice/ragi cereal
- Mashed dal with ghee
- Mashed banana
- Suji kheer
- Mashed potato with curd

9-11 MONTHS:
✓ 3-4 meals/day + 1-2 snacks
✓ Introduce family foods (finely chopped)
✓ Finger foods: Soft chapati pieces, steamed vegetables
✓ Continue breastfeeding

12-24 MONTHS:
✓ 3-4 meals/day + 2 snacks
✓ Same family foods, gradually increase texture
✓ Continue breastfeeding until 2 years+
✓ Minimum Dietary Diversity: 4+ food groups daily

7 FOOD GROUPS (for dietary diversity):
1. Grains: Rice, wheat, ragi, bajra
2. Legumes: Dal, rajma, chana
3. Dairy: Milk, curd, paneer
4. Eggs
5. Meat/Fish/Chicken
6. Fruits: Banana, mango, papaya, apple
7. Vegetables: Spinach, carrot, pumpkin, tomato

IRON-RICH FOODS (prevent anemia):
- Green leafy vegetables (palak, methi)
- Dal with vitamin C (lemon juice)
- Eggs
- Meat/chicken liver
- Jaggery (gur)
- Fortified cereals

FOODS TO AVOID <1 YEAR:
❌ Honey (botulism risk)
❌ Cow's milk as main drink (low iron)
❌ Salt, sugar (kidneys not mature)
❌ Whole nuts (choking hazard)
❌ Fruit juice (empty calories)

RESPONSIVE FEEDING PRACTICES:
✓ Feed slowly and patiently
✓ Encourage, don't force
✓ Eye contact while feeding
✓ Minimize distractions (no TV)
✓ Recognize hunger/fullness cues

GROWTH PROMOTION COUNSELING:

For UNDERWEIGHT child:
1. Frequent small meals (6x/day)
2. Energy-dense foods: Ghee, oil, nuts paste
3. Protein: Eggs, dal, paneer, chicken
4. Deworming if >1 year
5. Monitor weight every 2 weeks

For STUNTED child (long-term issue):
1. Increase dietary diversity
2. Ensure adequate protein
3. Vitamin/mineral supplements if prescribed
4. Infection prevention (hygiene, vaccines)
5. Developmental stimulation

For OVERWEIGHT child:
1. Reduce fried/junk foods
2. Limit screen time
3. Increase physical activity
4. No sugary drinks
5. Family-based approach (everyone eats healthy)

RESPONSE FORMAT:
1. Interpret z-scores in parent-friendly language
2. Classify growth status (normal/flagged/urgent)
3. Provide specific feeding recommendations
4. Give practical meal ideas
5. Escalate if severe malnutrition detected

Always respond in the parent's preferred language (Hindi/Marathi/English).
Use encouraging, non-shaming language.
Emphasize what parent is doing RIGHT."""
    
    
    async def calculate_z_scores(self, growth_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate WHO z-scores for weight, height, and head circumference
        
        Note: This is a simplified calculation. Production systems should use 
        WHO LMS (Lambda-Mu-Sigma) parameters from official WHO tables.
        
        Args:
            growth_data: Dict with weight_kg, height_cm, age_months, gender, head_circumference_cm
            
        Returns:
            Z-scores and growth status classification
        """
        weight_kg = growth_data.get('weight_kg', 0)
        height_cm = growth_data.get('height_cm', 0)
        age_months = growth_data.get('age_months', 0)
        gender = growth_data.get('gender', 'male').lower()
        head_circ_cm = growth_data.get('head_circumference_cm', 0)
        
        # Note: These are APPROXIMATE values for demonstration
        # Production should use official WHO LMS tables
        z_scores = {}
        growth_status = 'normal'
        alerts = []
        
        # Weight-for-age z-score (simplified estimation)
        if age_months <= 60:  # 0-5 years
            # Approximate median weights (WHO standards)
            median_weights = self._get_median_weight(age_months, gender)
            sd_weight = median_weights * 0.15  # Approximate SD
            
            if median_weights > 0:
                wfa_z = (weight_kg - median_weights) / sd_weight
                z_scores['weight_for_age_z_score'] = round(wfa_z, 2)
                
                if wfa_z < -3:
                    growth_status = 'severe_acute_malnutrition'
                    alerts.append("🚨 SEVERE UNDERWEIGHT - Urgent medical attention needed")
                elif wfa_z < -2:
                    growth_status = 'moderate_acute_malnutrition'
                    alerts.append("⚠️ MODERATE UNDERWEIGHT - Nutritional support needed")
                elif wfa_z > 2:
                    alerts.append("⚠️ OVERWEIGHT - Review feeding practices")
        
        # Height-for-age z-score (stunting indicator)
        if height_cm > 0 and age_months <= 60:
            median_height = self._get_median_height(age_months, gender)
            sd_height = median_height * 0.05  # Approximate SD
            
            if median_height > 0:
                hfa_z = (height_cm - median_height) / sd_height
                z_scores['height_for_age_z_score'] = round(hfa_z, 2)
                
                if hfa_z < -3:
                    if growth_status == 'normal':
                        growth_status = 'severely_stunted'
                    alerts.append("🚨 SEVERE STUNTING - Chronic malnutrition indicator")
                elif hfa_z < -2:
                    if growth_status == 'normal':
                        growth_status = 'stunted'
                    alerts.append("⚠️ MODERATE STUNTING - Long-term nutritional deficiency")
        
        # Weight-for-height z-score (acute malnutrition - wasting)
        if weight_kg > 0 and height_cm > 0:
            # This requires WHO lookup tables by height
            # Simplified estimation
            expected_weight = self._get_expected_weight_for_height(height_cm, gender)
            if expected_weight > 0:
                sd_wfh = expected_weight * 0.12
                wfh_z = (weight_kg - expected_weight) / sd_wfh
                z_scores['weight_for_height_z_score'] = round(wfh_z, 2)
                
                if wfh_z < -3:
                    growth_status = 'severe_acute_malnutrition'
                    alerts.append("🚨 SEVERE WASTING (SAM) - Emergency nutrition intervention")
                elif wfh_z < -2:
                    if 'acute' not in growth_status:
                        growth_status = 'moderate_acute_malnutrition'
                    alerts.append("⚠️ MODERATE WASTING (MAM) - Enhanced feeding needed")
                elif wfh_z > 3:
                    alerts.append("⚠️ OBESITY - Reduce calorie-dense foods, increase activity")
                elif wfh_z > 2:
                    alerts.append("⚠️ OVERWEIGHT - Monitor diet and activity")
        
        # Head circumference (critical 0-24 months)
        if head_circ_cm > 0 and age_months <= 24:
            median_hc = self._get_median_head_circumference(age_months, gender)
            if median_hc > 0:
                sd_hc = 1.5  # Approximate
                hc_z = (head_circ_cm - median_hc) / sd_hc
                z_scores['head_circumference_z_score'] = round(hc_z, 2)
                
                if hc_z < -2 or hc_z > 2:
                    alerts.append("⚠️ Head circumference outside normal - Medical checkup recommended")
        
        return {
            'z_scores': z_scores,
            'growth_status': growth_status,
            'alerts': alerts,
            'interpretation': self._interpret_z_scores(z_scores, growth_status)
        }
    
    async def assess_feeding_practices(self, feeding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess infant and young child feeding practices against WHO IYCF
        
        Args:
            feeding_data: Dict with age_months, breastfeeding_status, food_groups, meal_frequency
            
        Returns:
            Assessment and recommendations
        """
        age_months = feeding_data.get('age_months', 0)
        is_breastfeeding = feeding_data.get('is_breastfeeding', False)
        exclusive_bf = feeding_data.get('exclusive_breastfeeding', False)
        food_groups = feeding_data.get('food_groups_consumed', [])
        meal_frequency = feeding_data.get('meal_frequency_per_day', 0)
        
        recommendations = []
        issues = []
        
        # 0-6 months: Exclusive breastfeeding
        if age_months < 6:
            if not is_breastfeeding:
                issues.append("⚠️ Not breastfeeding - Breast milk is best nutrition for babies <6 months")
                recommendations.append("🤱 Start/restart breastfeeding if possible, seek lactation support")
            elif not exclusive_bf:
                issues.append("⚠️ Giving foods/water before 6 months")
                recommendations.append("✓ EXCLUSIVE breastfeeding (NO water, foods) until 6 months per WHO")
            else:
                recommendations.append("✅ EXCELLENT! Exclusive breastfeeding is perfect for baby's age")
        
        # 6-24 months: Complementary feeding
        elif age_months >= 6:
            # Check breastfeeding continuation
            if not is_breastfeeding and age_months < 24:
                recommendations.append("💛 Continue breastfeeding until 2 years+ for immunity and bonding")
            elif is_breastfeeding:
                recommendations.append("✅ Great! Continuing breastfeeding provides nutrition and immunity")
            
            # Meal frequency assessment
            if age_months < 9:
                recommended_meals = 3
            elif age_months < 12:
                recommended_meals = 4
            else:
                recommended_meals = 4
            
            if meal_frequency < recommended_meals:
                issues.append(f"⚠️ Only {meal_frequency} meals/day - Recommended: {recommended_meals}+")
                recommendations.append(f"🍽️ Increase to {recommended_meals} meals + 1-2 snacks per day")
            
            # Dietary diversity (WHO: ≥4 food groups)
            num_food_groups = len(food_groups)
            if num_food_groups < 4:
                issues.append(f"⚠️ Only {num_food_groups} food groups - Recommended: 4+ for complete nutrition")
                missing_groups = self._suggest_missing_food_groups(food_groups)
                recommendations.extend(missing_groups)
            else:
                recommendations.append(f"✅ EXCELLENT dietary diversity ({num_food_groups} food groups)")
            
            # Age-specific feeding guidance
            if age_months == 6:
                recommendations.append("\n🎉 Starting solids! Begin with:")
                recommendations.append("  • Mashed banana / Rice cereal / Dal water")
                recommendations.append("  • 2-3 tablespoons, 2-3 times/day")
                recommendations.append("  • Increase amount gradually")
            
            if age_months >= 6 and age_months <= 12:
                recommendations.append("\n🌾 IRON-RICH foods are CRITICAL now:")
                recommendations.append("  • Fortified cereals, dal with lemon, eggs")
                recommendations.append("  • Green leafy vegetables (palak), jaggery")
        
        return {
            'feeding_adequacy': 'adequate' if len(issues) == 0 else 'needs_improvement',
            'issues_identified': issues,
            'recommendations': recommendations,
            'meal_plan_suggestions': self._generate_meal_plan(age_months)
        }
    
    def _get_median_weight(self, age_months: int, gender: str) -> float:
        """Get approximate median weight from WHO standards"""
        # Simplified - production should use WHO LMS tables
        weights_male = {
            0: 3.3, 1: 4.5, 2: 5.6, 3: 6.4, 6: 7.9, 9: 9.2, 
            12: 10.2, 18: 11.8, 24: 12.9, 36: 14.7, 48: 16.7, 60: 18.9
        }
        weights_female = {
            0: 3.2, 1: 4.2, 2: 5.1, 3: 5.8, 6: 7.3, 9: 8.6,
            12: 9.5, 18: 11.0, 24: 12.1, 36: 13.9, 48: 16.0, 60: 18.2
        }
        
        weights = weights_male if gender == 'male' else weights_female
        
        # Find closest age in table
        closest_age = min(weights.keys(), key=lambda x: abs(x - age_months))
        return weights.get(closest_age, 10.0)
    
    def _get_median_height(self, age_months: int, gender: str) -> float:
        """Get approximate median height from WHO standards"""
        heights_male = {
            0: 49.9, 1: 54.7, 2: 58.4, 3: 61.4, 6: 67.6, 9: 72.0,
            12: 75.7, 18: 82.3, 24: 87.8, 36: 96.1, 48: 103.3, 60: 110.0
        }
        heights_female = {
            0: 49.1, 1: 53.7, 2: 57.1, 3: 59.8, 6: 65.7, 9: 70.1,
            12: 74.0, 18: 80.7, 24: 86.4, 36: 95.1, 48: 102.7, 60: 109.4
        }
        
        heights = heights_male if gender == 'male' else heights_female
        closest_age = min(heights.keys(), key=lambda x: abs(x - age_months))
        return heights.get(closest_age, 75.0)
    
    def _get_expected_weight_for_height(self, height_cm: float, gender: str) -> float:
        """Simplified weight-for-height estimation"""
        # Very simplified - production needs WHO WFH tables
        if gender == 'male':
            return (height_cm - 40) * 0.18
        else:
            return (height_cm - 40) * 0.17
    
    def _get_median_head_circumference(self, age_months: int, gender: str) -> float:
        """Get approximate median head circumference"""
        hc_male = {
            0: 34.5, 1: 37.3, 2: 39.1, 3: 40.5, 6: 43.3, 9: 45.0,
            12: 46.1, 18: 47.7, 24: 48.7
        }
        hc_female = {
            0: 33.9, 1: 36.5, 2: 38.3, 3: 39.5, 6: 42.2, 9: 43.8,
            12: 45.0, 18: 46.6, 24: 47.6
        }
        
        hc = hc_male if gender == 'male' else hc_female
        closest_age = min(hc.keys(), key=lambda x: abs(x - age_months))
        return hc.get(closest_age, 45.0)
    
    def _interpret_z_scores(self, z_scores: Dict[str, float], growth_status: str) -> str:
        """Provide parent-friendly interpretation"""
        interpretations = {
            'normal': "✅ Your child's growth is NORMAL and on track!",
            'moderate_acute_malnutrition': "⚠️ Moderate undernutrition detected - Enhanced feeding needed",
            'severe_acute_malnutrition': "🚨 Severe malnutrition - Urgent medical care required",
            'stunted': "⚠️ Moderate stunting - Long-term nutritional improvement needed",
            'severely_stunted': "🚨 Severe stunting - Comprehensive intervention required",
            'at_risk': "💛 Growth needs monitoring - Focus on nutritious foods"
        }
        
        return interpretations.get(growth_status, "Growth assessment completed")
    
    def _suggest_missing_food_groups(self, current_groups: List[str]) -> List[str]:
        """Suggest missing food groups"""
        all_groups = {
            'grains': "🌾 Add: Rice, roti, ragi, poha",
            'legumes': "🫘 Add: Dal (moong, masoor), rajma, chana",
            'dairy': "🥛 Add: Milk, curd, paneer, cheese",
            'eggs': "🥚 Add: Boiled egg (rich in protein & iron)",
            'meat': "🍗 Add: Chicken, fish, mutton (if non-veg)",
            'fruits': "🍎 Add: Banana, mango, papaya, apple",
            'vegetables': "🥕 Add: Carrot, spinach, pumpkin, beans"
        }
        
        suggestions = []
        for group, suggestion in all_groups.items():
            if group not in current_groups:
                suggestions.append(suggestion)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _generate_meal_plan(self, age_months: int) -> Dict[str, List[str]]:
        """Generate sample meal plan for age"""
        if age_months < 6:
            return {
                'all_meals': ["Exclusive breastfeeding on demand (8-12 times/day)"]
            }
        
        elif age_months >= 6 and age_months < 9:
            return {
                'breakfast': ["Ragi porridge with ghee", "Banana mashed"],
                'lunch': ["Rice + moong dal khichdi + ghee", "Mashed potato with curd"],
                'evening': ["Suji kheer", "Apple puree"],
                'dinner': ["Mashed rice with dal", "Carrot puree"],
                'note': "Continue breastfeeding on demand"
            }
        
        elif age_months >= 9 and age_months < 12:
            return {
                'breakfast': ["Idli with sambar", "Dalia with milk"],
                'lunch': ["Khichdi with vegetables + curd", "Rice + dal + ghee"],
                'snack': ["Banana", "Biscuit with milk"],
                'dinner': ["Soft roti with dal", "Rice with mashed sabzi"],
                'note': "Include egg 3-4 times/week"
            }
        
        else:  # 12+ months
            return {
                'breakfast': ["Paratha with curd", "Poha", "Upma"],
                'lunch': ["Rice + dal + sabzi + roti", "Khichdi with vegetables"],
                'snack': ["Fruits", "Boiled egg", "Milk with biscuits"],
                'dinner': ["Family foods (softer version)", "Rice + curry + curd"],
                'note': "Same as family meals, ensure dietary diversity"
            }
    
    def generate_response(
        self, 
        message: str, 
        child_context: Dict[str, Any],
        growth_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextual response to growth/nutrition query"""
        if not GEMINI_AVAILABLE or not self.model:
            return self._fallback_response(message)
        
        context_parts = [
            f"Child: {child_context.get('name', 'Unknown')}",
            f"Age: {child_context.get('age_months', 'Unknown')} months",
            f"Current weight: {child_context.get('weight_kg', 'Unknown')} kg",
            f"Language: {child_context.get('preferred_language', 'English')}"
        ]
        
        if growth_data:
            context_parts.append(f"Growth status: {growth_data.get('growth_status', 'Unknown')}")
        
        full_prompt = f"""Context:
{chr(10).join(context_parts)}

Parent's question: {message}

Provide evidence-based nutrition guidance following WHO IYCF guidelines.
Include practical, culturally-appropriate food suggestions."""

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"GrowthAgent Gemini error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response"""
        return """I'm your child growth & nutrition guide!

I can help with:
📊 **Growth tracking** - Is my child's weight/height normal?
🍽️ **Feeding guidance** - What foods to give at this age?
🥗 **Meal plans** - Sample nutritious meals
⚠️ **Malnutrition screening** - Growth concerns

💡 KEY TIPS:
- 0-6 months: EXCLUSIVE breastfeeding
- 6+ months: Continue BF + complementary foods
- 4+ food groups daily for complete nutrition
- Iron-rich foods prevent anemia

What would you like to know?"""
