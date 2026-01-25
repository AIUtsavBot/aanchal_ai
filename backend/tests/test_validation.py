"""
MatruRaksha - Input Validation Tests
Test input validation and sanitization
"""

import pytest
from models.validators import (
    sanitize_text,
    normalize_phone_number,
    sanitize_filename,
    validate_email
)


@pytest.mark.unit
class TestTextSanitization:
    """Test text sanitization"""
    
    def test_removes_html_tags(self):
        """Test HTML tags are removed"""
        dirty = "<script>alert('xss')</script>Hello"
        clean = sanitize_text(dirty)
        assert "<script>" not in clean
        assert "Hello" in clean
    
    def test_removes_extra_whitespace(self):
        """Test extra whitespace is removed"""
        dirty = "Hello    World"
        clean = sanitize_text(dirty)
        assert clean == "Hello World"
    
    def test_handles_empty_string(self):
        """Test empty string handling"""
        assert sanitize_text("") == ""
        assert sanitize_text(None) is None


@pytest.mark.unit
class TestPhoneNormalization:
    """Test phone number normalization"""
    
    def test_adds_country_code_to_10_digit(self):
        """Test 10-digit number gets +91"""
        phone = "9876543210"
        normalized = normalize_phone_number(phone)
        assert normalized == "+919876543210"
    
    def test_handles_12_digit_with_91(self):
        """Test 12-digit starting with 91"""
        phone = "919876543210"
        normalized = normalize_phone_number(phone)
        assert normalized == "+919876543210"
    
    def test_removes_special_characters(self):
        """Test special characters are removed"""
        phone = "+91 (987) 654-3210"
        normalized = normalize_phone_number(phone)
        assert "(" not in normalized
        assert ")" not in normalized
        assert "-" not in normalized
    
    def test_handles_empty_phone(self):
        """Test empty phone number"""
        assert normalize_phone_number("") == ""
        assert normalize_phone_number(None) is None


@pytest.mark.unit
class TestEmailValidation:
    """Test email validation"""
    
    def test_validates_correct_email(self):
        """Test valid email passes"""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.in") is True
    
    def test_rejects_invalid_email(self):
        """Test invalid email fails"""
        assert validate_email("notanemail") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False


@pytest.mark.unit
class TestFilenameSanitization:
    """Test filename sanitization"""
    
    def test_removes_path_separators(self):
        """Test path separators are removed"""
        filename = "../../../etc/passwd"
        sanitized = sanitize_filename(filename)
        assert "/" not in sanitized
        assert "\\" not in sanitized
    
    def test_removes_dangerous_characters(self):
        """Test dangerous characters are replaced"""
        filename = "file<>name:*.txt"
        sanitized = sanitize_filename(filename)
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert "*" not in sanitized
    
    def test_limits_length(self):
        """Test filename length is limited"""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
