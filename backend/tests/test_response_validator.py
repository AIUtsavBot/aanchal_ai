"""
MatruRaksha - Response Validator Tests
Test AI response validation against clinical rules
"""

import pytest
from services.response_validator import (
    ClinicalRulesValidator,
    validate_response,
    ValidationSeverity,
    ValidationResult,
    get_validator
)


@pytest.fixture
def validator():
    """Get validator instance"""
    return ClinicalRulesValidator()


@pytest.mark.unit
class TestContraband:
    """Test contraband phrase detection"""
    
    def test_detects_aspirin_for_fever(self, validator):
        """Test aspirin recommendation is flagged"""
        response = "You can give aspirin for fever if the child is uncomfortable."
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL
        assert any("aspirin" in issue.lower() for issue in result.issues)
    
    def test_detects_honey_for_infant(self, validator):
        """Test honey for infant is flagged"""
        response = "Give honey to baby to soothe the cough."
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL
        assert any("honey" in issue.lower() or "botulism" in issue.lower() for issue in result.issues)
    
    def test_detects_cold_bath(self, validator):
        """Test cold water bath is flagged"""
        response = "Try a cold water bath to bring down the fever quickly."
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL
    
    def test_detects_skip_vaccine(self, validator):
        """Test anti-vaccination advice is flagged"""
        response = "You can skip vaccine if your child seems healthy."
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL
    
    def test_detects_autism_myth(self, validator):
        """Test autism-vaccine myth is flagged"""
        response = "Some believe vaccines cause autism so be careful."
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL


@pytest.mark.unit  
class TestCitations:
    """Test citation detection and requirements"""
    
    def test_extracts_source_citation(self, validator):
        """Test correctly formed citations are extracted"""
        response = "Give ORS 75ml/kg over 4 hours [SOURCE: WHO ORS Plan B]"
        result = validator.validate_response(response)
        
        assert not result.citations_missing
        assert "WHO ORS Plan B" in result.citations_found
    
    def test_extracts_multiple_citations(self, validator):
        """Test multiple citations are extracted"""
        response = """
        For fever in infants under 3 months, seek care immediately [SOURCE: IMNCI].
        The vaccination schedule follows [SOURCE: IAP 2023].
        """
        result = validator.validate_response(response)
        
        assert len(result.citations_found) == 2
        assert "IMNCI" in result.citations_found
        assert "IAP 2023" in result.citations_found
    
    def test_flags_missing_citation_for_medical_advice(self, validator):
        """Test medical advice without citation is flagged"""
        response = "Give paracetamol 10-15mg/kg every 4-6 hours for fever."
        result = validator.validate_response(response)
        
        # Should have warning about missing citation (not critical)
        assert result.citations_missing
        assert any("citation" in issue.lower() for issue in result.issues)
    
    def test_allows_non_medical_without_citation(self, validator):
        """Test non-medical responses don't need citations"""
        response = "Hello! I'm here to help you with your questions."
        result = validator.validate_response(response)
        
        # Non-medical response is valid without citation
        assert result.is_valid


@pytest.mark.unit
class TestSafeResponses:
    """Test safe responses pass validation"""
    
    def test_safe_fever_advice_passes(self, validator):
        """Test proper fever advice passes"""
        response = """
        For fever, you can give paracetamol as your doctor recommended [SOURCE: IMNCI].
        Use lukewarm water sponging, not cold water.
        If fever persists for more than 3 days, consult your healthcare provider.
        """
        result = validator.validate_response(response)
        
        # Should pass - has citation, no contraband
        assert result.is_valid
        assert result.severity != ValidationSeverity.CRITICAL
    
    def test_safe_vaccination_advice_passes(self, validator):
        """Test proper vaccination advice passes"""
        response = """
        As per IAP 2023 schedule, your child should receive the following vaccines [SOURCE: IAP 2023]:
        - At birth: BCG, OPV-0, Hepatitis B
        - At 6 weeks: Pentavalent, OPV, Rotavirus
        Please visit your nearest PHC for vaccinations.
        """
        result = validator.validate_response(response)
        
        assert result.is_valid


@pytest.mark.unit
class TestFallbackResponse:
    """Test safe fallback is returned for critical issues"""
    
    def test_fallback_for_contraband(self, validator):
        """Test fallback is provided for contraband"""
        response = "Give aspirin for fever in your child."
        result = validator.validate_response(response)
        
        assert result.modified_response is not None
        assert "healthcare provider" in result.modified_response.lower()
        assert "108" in result.modified_response  # Emergency number
    
    def test_disclaimer_for_warnings(self, validator):
        """Test disclaimer is added for warning issues"""
        response = "Give paracetamol 10mg/kg for fever."  # No citation
        result = validator.validate_response(response)
        
        if result.severity == ValidationSeverity.WARNING:
            assert result.modified_response is not None
            assert "consult" in result.modified_response.lower() or "disclaimer" in result.modified_response.lower() or "note" in result.modified_response.lower()


@pytest.mark.unit
class TestValidatorSingleton:
    """Test validator singleton pattern"""
    
    def test_singleton_returns_same_instance(self):
        """Test get_validator returns same instance"""
        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2
    
    def test_convenience_function_works(self):
        """Test validate_response convenience function"""
        result = validate_response("Hello, how can I help?")
        assert isinstance(result, ValidationResult)
