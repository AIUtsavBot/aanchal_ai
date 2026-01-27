
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

# Services
try:
    from services.supabase_service import supabase
except ImportError:
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

try:
    from services.cache_service import cache
except ImportError:
    cache = None

logger = logging.getLogger(__name__)

class AIPredictionService:
    """
    Advanced AI Service for Health Intelligence.
    Combines Deterministic Rules (Clinical compatibility) with 
    Probabilistic Models (Trend analysis) and GenAI (Summarization).
    """

    @staticmethod
    async def analyze_mother_risk(mother_id: str) -> Dict:
        """
        Comprehensive risk analysis for a mother.
        Returns a risk profile and saves it to patient_insights.
        """
        try:
            # 1. Fetch Data (Parallel)
            mother_task = supabase.table("mothers").select("*").eq("id", mother_id).single().execute()
            assessments_task = supabase.table("risk_assessments") \
                .select("*") \
                .eq("mother_id", mother_id) \
                .order("created_at", desc=True) \
                .limit(5) \
                .execute()
            
            results = await asyncio.gather(
                asyncio.to_thread(lambda: mother_task),
                asyncio.to_thread(lambda: assessments_task), 
                return_exceptions=True
            )
            
            mother_res = results[0]
            assess_res = results[1]
            
            if isinstance(mother_res, Exception) or not mother_res.data:
                raise ValueError("Mother not found")
                
            mother = mother_res.data
            assessments = assess_res.data or []
            
            # 2. Risk Calculation Engine
            clinical_risk = AIPredictionService._calculate_clinical_risk(mother, assessments)
            trend_risk = AIPredictionService._calculate_trend_risk(assessments)
            
            # Combine risks (Max strategy - be conservative)
            final_risk_level = "LOW"
            if clinical_risk["level"] == "HIGH" or trend_risk["level"] == "HIGH":
                final_risk_level = "HIGH"
            elif clinical_risk["level"] == "MODERATE" or trend_risk["level"] == "MODERATE":
                final_risk_level = "MODERATE"
                
            combined_factors = clinical_risk["factors"] + trend_risk["factors"]
            
            insight = {
                "mother_id": mother_id,
                "type": "RISK_ASSESSMENT",
                "severity": final_risk_level,
                "confidence_score": 0.85 if assessments else 0.5, # Lower confidence if no history
                "summary": f"Assessment for {mother.get('name')}: {final_risk_level} Risk. {', '.join(combined_factors)}.",
                "details": {
                    "clinical_risk": clinical_risk,
                    "trend_risk": trend_risk,
                    "vital_trends": trend_risk.get("metrics", {})
                },
                "generated_at": datetime.now().isoformat()
            }
            
            # 3. Store Insight
            await asyncio.to_thread(lambda: supabase.table("patient_insights").insert(insight).execute())
            
            return insight
            
        except Exception as e:
            logger.error(f"Prediction analysis failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_clinical_risk(mother: Dict, assessments: List[Dict]) -> Dict:
        """Deterministic rules based on medical guidelines (IMNCI/WHO)"""
        factors = []
        score = 0
        
        # Static Factors
        age = mother.get("age", 25)
        if age < 18 or age > 35:
            score += 1
            factors.append("Maternal Age Risk")
            
        parity = mother.get("parity", 0)
        if parity > 4:
            score += 1
            factors.append("Grand Multipara")
            
        # Dynamic Factors (Latest Assessment)
        if assessments:
            latest = assessments[0]
            
            # BP
            sys = latest.get("systolic_bp") or 120
            dia = latest.get("diastolic_bp") or 80
            if sys >= 140 or dia >= 90:
                score += 3 # High impact
                factors.append("Hypertension")
                
            # Hemoglobin
            hb = latest.get("hemoglobin")
            if hb and hb < 10:
                score += 2
                factors.append("Anemia")
                
            # Symptoms
            if latest.get("proteinuria"): factors.append("Proteinuria")
            if latest.get("vaginal_bleeding"): score += 5; factors.append("Vaginal Bleeding (Emergency)")
            
        level = "LOW"
        if score >= 5: level = "HIGH"
        elif score >= 2: level = "MODERATE"
        
        return {"level": level, "score": score, "factors": factors}

    @staticmethod
    def _calculate_trend_risk(assessments: List[Dict]) -> Dict:
        """Analyze trends over last N visits (e.g. rising BP)"""
        if len(assessments) < 2:
            return {"level": "LOW", "factors": [], "metrics": {}}
            
        # Sort ascending time
        assessments = sorted(assessments, key=lambda x: x['created_at'])
        
        factors = []
        metrics = {"bp_trend": "stable", "weight_trend": "stable"}
        level = "LOW"
        
        # BP Trend
        sys_values = [a.get("systolic_bp") for a in assessments if a.get("systolic_bp")]
        if len(sys_values) >= 2:
            # Check if constantly increasing
            if all(y > x for x, y in zip(sys_values, sys_values[1:])):
                metrics["bp_trend"] = "increasing"
                # If increase is significant (>10 spread)
                if sys_values[-1] - sys_values[0] > 15:
                    factors.append("Rapid BP Increase")
                    level = "MODERATE"
        
        return {"level": level, "factors": factors, "metrics": metrics}

    @staticmethod
    async def generate_health_summary(mother_id: str, gemini_client) -> Dict:
        """
        Use GenAI to generate a human-readable health summary 
        digestible by doctors/workers.
        """
        try:
            # Fetch Context similar to analyze_risk...
            # (Skipping duplicate fetch logic for brevity - in prod would refactor to shared data loader)
            mother_res = supabase.table("mothers").select("*").eq("id", mother_id).single().execute()
            mother = mother_res.data
            
            assessments_res = supabase.table("risk_assessments").select("*").eq("mother_id", mother_id).limit(3).execute()
            history = assessments_res.data or []
            
            if not gemini_client:
                return {"error": "AI not available"}
                
            # Construct Prompt
            prompt = f"""
            Act as a senior Obstetrician. Generate a concise 3-sentence clinical summary for this patient.
            
            Patient: {mother.get('name')}, Age: {mother.get('age')}, G{mother.get('gravida')}P{mother.get('parity')}
            
            Recent Vitals History (Latest First):
            {json.dumps(history, default=str)}
            
            Format:
            1. Current Status: (Stable/Concerns)
            2. Key Risk Factors: (List or 'None')
            3. Recommendation: (Next steps)
            """
            
            # Generate
            response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            
            summary_text = response.text
            
            insight = {
                "mother_id": mother_id,
                "type": "HEALTH_SUMMARY",
                "summary": summary_text,
                "confidence_score": 1.0,
                "generated_at": datetime.now().isoformat()
            }
            
            # Store
            await asyncio.to_thread(lambda: supabase.table("patient_insights").insert(insight).execute())
            
            return insight
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"error": str(e)}
