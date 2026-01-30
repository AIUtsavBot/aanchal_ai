"""
MatruRaksha/SantanRaksha - AI Response Validator

Post-validates AI responses against clinical rules to prevent hallucination.
Enforces citation requirements for medical recommendations.

Clinical Sources:
- IMNCI (Integrated Management of Neonatal and Childhood Illness)
- IAP 2023 (Indian Academy of Pediatrics Immunization Schedule)
- WHO Growth Standards
- WHO ORS Plans A/B/C
- NHM SUMAN (Postnatal Care)
- WHO IYCF (Infant and Young Child Feeding)
- EPDS (Edinburgh Postnatal Depression Scale)
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"           # Minor issue, log only
    WARNING = "warning"     # Add disclaimer to response
    CRITICAL = "critical"   # Block response, use fallback
    

@dataclass
class ValidationResult:
    """Result of response validation"""
    is_valid: bool
    severity: ValidationSeverity
    issues: List[str]
    citations_found: List[str]
    citations_missing: bool
    modified_response: Optional[str] = None


class ClinicalRulesValidator:
    """
    Validates AI responses against hardcoded clinical rules.
    Prevents dangerous medical advice from being sent to users.
    """
    
    # ==================== CONTRABAND PHRASES ====================
    # Phrases that should NEVER appear in responses to mothers
    CONTRABAND_PHRASES = {
        # Medication safety
        "aspirin for fever": "Aspirin can cause Reye's syndrome in children",
        "aspirin for child": "Aspirin can cause Reye's syndrome in children",
        "give aspirin": "Aspirin is contraindicated for children with fever",
        
        # Feeding safety
        "honey before 1 year": "Honey can cause infant botulism",
        "honey for infant": "Honey can cause infant botulism under 12 months",
        "honey under 12 month": "Honey is contraindicated for infants",
        "give honey to baby": "Honey can cause botulism in infants <1 year",
        
        # Medication contraindications
        "cough syrup under 2": "Cough syrups are not recommended for children under 2 years",
        "cough medicine for infant": "Cough medicines are not effective for infants",
        "decongestant for baby": "Decongestants are not recommended for infants",
        
        # Fever management
        "cold water bath": "Cold baths can cause shivering and raise temperature",
        "ice bath for fever": "Ice baths are dangerous and contraindicated",
        "alcohol rub": "Alcohol rubs can cause poisoning through skin absorption",
        
        # Anti-vaccination
        "skip vaccine": "Vaccines are essential for child health",
        "avoid vaccination": "Vaccines prevent serious diseases",
        "vaccines cause autism": "This is a debunked myth - vaccines do not cause autism",
        "don't vaccinate": "Vaccination is recommended by IAP and WHO",
        
        # Dangerous advice
        "give antibiotics without doctor": "Antibiotics require medical prescription",
        "home remedy instead of hospital": "Seek medical care for emergencies",
        "wait and see for emergency": "Emergency symptoms require immediate care",
    }
    
    # ==================== CLINICAL THRESHOLDS ====================
    # Numeric thresholds from clinical guidelines
    FEVER_THRESHOLDS = {
        "infant_0_3_months": {"temp_c": 37.5, "action": "immediate_hospital", "source": "IMNCI"},
        "infant_3_6_months": {"temp_c": 38.3, "action": "doctor_today", "source": "IMNCI"},
        "child_over_6_months": {"temp_c": 39.4, "action": "doctor_if_persists", "source": "IMNCI"},
    }
    
    BREATHING_THRESHOLDS = {
        "0_2_months": {"rate": 60, "source": "IMNCI"},
        "2_12_months": {"rate": 50, "source": "IMNCI"},
        "1_5_years": {"rate": 40, "source": "IMNCI"},
    }
    
    Z_SCORE_THRESHOLDS = {
        "severe_malnutrition": {"z": -3, "source": "WHO Growth Standards"},
        "moderate_malnutrition": {"z": -2, "source": "WHO Growth Standards"},
        "overweight": {"z": 2, "source": "WHO Growth Standards"},
        "obese": {"z": 3, "source": "WHO Growth Standards"},
    }
    
    ORS_DOSAGES = {
        "plan_a": {"ml_per_stool": "50-100ml", "source": "WHO ORS Plan A"},
        "plan_b": {"ml_per_kg": 75, "duration_hours": 4, "source": "WHO ORS Plan B"},
    }
    
    # ==================== VALID CITATION SOURCES ====================
    VALID_SOURCES = [
        "IMNCI",
        "IAP 2023",
        "IAP",
        "WHO Growth Standards",
        "WHO",
        "WHO ORS",
        "WHO IYCF",
        "NHM SUMAN",
        "NHM",
        "EPDS",
        "RBSK",
        "AAP",  # American Academy of Pediatrics (for sleep)
    ]
    
    # Citation regex pattern: [SOURCE: xxx] or [Source: xxx] or (Source: xxx)
    CITATION_PATTERN = r'\[(?:SOURCE|Source|source):\s*([^\]]+)\]|\((?:SOURCE|Source|source):\s*([^\)]+)\)'
    
    def __init__(self):
        logger.info("✅ Clinical Rules Validator initialized")
    
    def validate_response(
        self,
        response: str,
        context: Optional[Dict[str, Any]] = None,
        agent_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate an AI response against clinical rules.
        
        Args:
            response: The AI-generated response text
            context: Optional context (mother/child data, query type)
            agent_type: Type of agent that generated the response
            
        Returns:
            ValidationResult with validity status and any issues found
        """
        issues = []
        severity = ValidationSeverity.INFO
        response_lower = response.lower()
        
        # ==================== 1. CONTRABAND CHECK ====================
        contraband_found = self._check_contraband(response_lower)
        if contraband_found:
            issues.extend(contraband_found)
            severity = ValidationSeverity.CRITICAL
            logger.warning(f"🚨 CONTRABAND detected in AI response: {contraband_found}")
        
        # ==================== 2. DANGEROUS ADVICE CHECK ====================
        dangerous = self._check_dangerous_advice(response_lower, context)
        if dangerous:
            issues.extend(dangerous)
            if severity != ValidationSeverity.CRITICAL:
                severity = ValidationSeverity.WARNING
        
        # ==================== 3. CITATION CHECK ====================
        citations_found = self._extract_citations(response)
        citations_missing = len(citations_found) == 0
        
        # Medical recommendations should have citations
        has_medical_advice = self._contains_medical_advice(response_lower)
        if has_medical_advice and citations_missing:
            issues.append("Response contains medical advice without source citation")
            if severity == ValidationSeverity.INFO:
                severity = ValidationSeverity.WARNING
        
        # ==================== 4. THRESHOLD VALIDATION ====================
        threshold_issues = self._validate_thresholds(response, context)
        if threshold_issues:
            issues.extend(threshold_issues)
            if severity == ValidationSeverity.INFO:
                severity = ValidationSeverity.WARNING
        
        # Determine overall validity
        is_valid = severity != ValidationSeverity.CRITICAL
        
        # Generate modified response if needed
        modified_response = None
        if severity == ValidationSeverity.WARNING and issues:
            modified_response = self._add_disclaimer(response, issues)
        elif severity == ValidationSeverity.CRITICAL:
            modified_response = self._get_safe_fallback(context, agent_type)
        
        return ValidationResult(
            is_valid=is_valid,
            severity=severity,
            issues=issues,
            citations_found=citations_found,
            citations_missing=citations_missing,
            modified_response=modified_response
        )
    
    def _check_contraband(self, response_lower: str) -> List[str]:
        """Check for contraband phrases that should never appear"""
        found = []
        for phrase, reason in self.CONTRABAND_PHRASES.items():
            if phrase in response_lower:
                found.append(f"CONTRABAND: '{phrase}' - {reason}")
        return found
    
    def _check_dangerous_advice(
        self, 
        response_lower: str, 
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Check for contextually dangerous advice"""
        issues = []
        
        # Check for "don't go to hospital" when symptoms are serious
        if "don't" in response_lower and "hospital" in response_lower:
            if context:
                # If there are emergency keywords in context, this is dangerous
                emergency_terms = ['bleeding', 'unconscious', 'seizure', 'not breathing']
                query = context.get('query', '').lower()
                if any(term in query for term in emergency_terms):
                    issues.append("Potentially dangerous: Advising against hospital during emergency")
        
        # Check for "wait and watch" with critical symptoms
        if "wait" in response_lower and "watch" in response_lower:
            if context:
                query = context.get('query', '').lower()
                critical_terms = ['high fever', 'severe pain', 'blood', 'not moving']
                if any(term in query for term in critical_terms):
                    issues.append("Warning: 'Wait and watch' advice for potentially critical symptom")
        
        return issues
    
    def _extract_citations(self, response: str) -> List[str]:
        """Extract citation sources from response"""
        citations = []
        matches = re.findall(self.CITATION_PATTERN, response)
        for match in matches:
            # Each match is a tuple (group1, group2) from the regex
            source = match[0] if match[0] else match[1]
            if source:
                citations.append(source.strip())
        return citations
    
    def _contains_medical_advice(self, response_lower: str) -> bool:
        """Check if response contains medical advice that needs citation"""
        medical_indicators = [
            "give ", "dose", "mg/kg", "ml", "take ", "medicine",
            "hospital", "doctor", "emergency", "treatment",
            "vaccine", "immunization", "ors", "zinc",
            "paracetamol", "ibuprofen", "antibiotic",
            "breastfeed", "formula", "feeding",
            "danger sign", "seek care", "immediately"
        ]
        return any(indicator in response_lower for indicator in medical_indicators)
    
    def _validate_thresholds(
        self, 
        response: str, 
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Validate numeric thresholds in response match clinical guidelines"""
        issues = []
        response_lower = response.lower()
        
        # Check fever thresholds mentioned in response
        # Look for patterns like "fever above 38" or "temperature over 39"
        fever_pattern = r'(?:fever|temperature)\s*(?:above|over|>|greater than)\s*(\d+\.?\d*)'
        fever_matches = re.findall(fever_pattern, response_lower)
        
        for temp in fever_matches:
            temp_val = float(temp)
            # If response says fever is safe above 39.5 for young infants, flag it
            if context:
                age_months = context.get('age_months', 12)
                if age_months < 3 and temp_val > 37.5:
                    issues.append(
                        f"Threshold issue: Response mentions {temp_val}°C for infant <3 months. "
                        f"IMNCI: ANY fever requires immediate care."
                    )
        
        return issues
    
    def _add_disclaimer(self, response: str, issues: List[str]) -> str:
        """Add disclaimer for responses with warnings"""
        disclaimer = "\n\n⚠️ _Note: This guidance is for informational purposes. Always consult your healthcare provider for personalized medical advice._"
        
        # Add citation reminder if missing
        if any("citation" in issue.lower() for issue in issues):
            disclaimer += "\n📚 _Clinical guidelines referenced: IMNCI, WHO, IAP 2023_"
        
        return response + disclaimer
    
    def _get_safe_fallback(
        self, 
        context: Optional[Dict[str, Any]], 
        agent_type: Optional[str]
    ) -> str:
        """Return safe fallback response when validation fails critically"""
        return (
            "⚠️ I want to make sure I give you accurate information. "
            "For this question, I recommend speaking directly with your healthcare provider "
            "or ASHA worker who can give you personalized guidance.\n\n"
            "📞 If this is urgent, please contact:\n"
            "• Your doctor or nearest hospital\n"
            "• Emergency: 108 (Ambulance)\n"
            "• Your assigned ASHA worker"
        )
    
    def add_citations_to_response(self, response: str, sources_used: List[str]) -> str:
        """
        Add citation footer to response if citations are missing.
        Called after validation to ensure citations are present.
        """
        existing_citations = self._extract_citations(response)
        
        if not existing_citations and sources_used:
            citation_footer = "\n\n📚 _Sources: " + ", ".join(sources_used) + "_"
            return response + citation_footer
        
        return response


# Singleton instance
_validator = None

def get_validator() -> ClinicalRulesValidator:
    """Get or create global validator instance"""
    global _validator
    if _validator is None:
        _validator = ClinicalRulesValidator()
    return _validator


def validate_response(
    response: str,
    context: Optional[Dict[str, Any]] = None,
    agent_type: Optional[str] = None
) -> ValidationResult:
    """Convenience function for validating responses"""
    validator = get_validator()
    return validator.validate_response(response, context, agent_type)
