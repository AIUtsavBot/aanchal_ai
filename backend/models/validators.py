"""
MatruRaksha - Input Validators
Custom validators for data sanitization and normalization
"""

import re
import bleach
from typing import Optional
from pydantic import validator


def sanitize_text(text: str) -> str:
    """
    Sanitize text input by removing HTML tags and scripts
    """
    if not text:
        return text
    
    # Remove all HTML tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    
    # Remove extra whitespace
    cleaned = " ".join(cleaned.split())
    
    return cleaned


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format
    Accepts various formats and converts to +91XXXXXXXXXX
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if len(digits) == 10:
        # Indian mobile without country code
        return f"+91{digits}"
    elif len(digits) == 12 and digits.startswith("91"):
        # Already has country code
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith("091"):
        # Has 0 prefix
        return f"+{digits[1:]}"
    else:
        # Return as is if format is unexpected
        return phone


def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection
    """
    if not filename:
        return filename
    
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


class NameValidator:
    """Validator for name fields"""
    
    @staticmethod
    @validator('name', always=True)
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Sanitize
        v = sanitize_text(v)
        
        # Check length
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Name must be less than 100 characters')
        
        # Check for valid characters (allow letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s'-]+$", v):
            raise ValueError('Name contains invalid characters')
        
        return v


class PhoneValidator:
    """Valiator for phone number fields"""
    
    @staticmethod
    @validator('phone', always=True)
    def validate_phone(cls, v):
        if not v:
            raise ValueError('Phone number is required')
        
        # Normalize
        v = normalize_phone_number(v)
        
        # Validate E.164 format
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        
        return v


class AgeValidator:
    """Validator for age fields"""
    
    @staticmethod
    @validator('age', always=True)
    def validate_age(cls, v):
        if v is None:
            raise ValueError('Age is required')
        
        if v < 15 or v > 50:
            raise ValueError('Age must be between 15 and 50 for maternal health')
        
        return v
