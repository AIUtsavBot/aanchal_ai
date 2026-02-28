"""
ID Document Verification Service
Parses PAN Card, Aadhaar Card, Driving License in ANY language
Extracts: Name, DOB, ID Number, Address

Used for:
- ASHA worker registration (age verification, identity proof)
- Doctor verification (supplementary ID)
"""

import os
import io
import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    gemini_client = None

try:
    from PIL import Image
except ImportError:
    Image = None


class IDDocumentType(Enum):
    PAN_CARD = "pan_card"
    AADHAAR_CARD = "aadhaar_card"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    PASSPORT = "passport"
    UNKNOWN = "unknown"


@dataclass
class IDDocumentInfo:
    """Extracted information from an ID document"""
    document_type: IDDocumentType
    full_name: str
    date_of_birth: Optional[str]  # YYYY-MM-DD format
    id_number: str
    address: Optional[str]
    gender: Optional[str]
    father_name: Optional[str]
    issue_date: Optional[str]
    expiry_date: Optional[str]
    document_language: str
    confidence_score: float
    raw_extracted_text: str
    
    def calculate_age(self) -> Optional[int]:
        """Calculate age from DOB"""
        if not self.date_of_birth:
            return None
        try:
            dob = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except (ValueError, TypeError):
            return None


class IDDocumentVerificationService:
    """
    Service for parsing ID documents.
    
    Supports:
    - PAN Card (India)
    - Aadhaar Card (India)
    - Driving License
    - Documents in any language (Hindi, Tamil, etc.)
    """
    
    # Age requirements - HIDDEN from users
    AGE_REQUIREMENTS = {
        "ASHA_WORKER": 21,  # Minimum 21 years for ASHA worker
        "DOCTOR": 24,       # Minimum 24 years for doctor (after MBBS)
    }
    
    def __init__(self):
        self.gemini = gemini_client
        self.model_name = "gemini-2.5-flash"
    
    async def parse_id_document(
        self,
        file_bytes: bytes,
        filename: str
    ) -> IDDocumentInfo:
        """
        Parse an ID document image in ANY language.
        Extracts name, DOB, ID number, and other details.
        """
        if not self.gemini:
            raise ValueError("Gemini API not configured. Set GEMINI_API_KEY.")
        
        logger.info(f"🪪 Parsing ID document: {filename}")
        
        try:
            if Image is None:
                raise ImportError("PIL not installed")
            
            image = Image.open(io.BytesIO(file_bytes))
            
            # Multilingual ID parsing prompt
            prompt = """You are an expert document parser. Analyze this ID document image.
The document may be in ANY language (Hindi, Tamil, Marathi, English, etc.).

SUPPORTED DOCUMENTS:
- PAN Card (India) - 10 character alphanumeric
- Aadhaar Card (India) - 12 digit number
- Driving License - Format varies by state
- Voter ID - EPIC number
- Passport

Extract ALL information and return in this EXACT JSON format:
{
    "document_type": "pan_card|aadhaar_card|driving_license|voter_id|passport|unknown",
    "full_name": "Full name as written on document (in English if possible)",
    "date_of_birth": "YYYY-MM-DD format or null",
    "id_number": "The main ID number (PAN/Aadhaar/DL number)",
    "address": "Full address if visible or null",
    "gender": "Male|Female|Other or null",
    "father_name": "Father's name if visible or null",
    "issue_date": "YYYY-MM-DD format or null",
    "expiry_date": "YYYY-MM-DD format or null (for DL, Passport)",
    "document_language": "Primary language of the document",
    "raw_text": "Key text extracted from the document",
    "confidence": "0.0 to 1.0 confidence score"
}

IMPORTANT:
- Return ONLY valid JSON
- Convert dates to YYYY-MM-DD format
- Transliterate names to English if in regional language
- Extract ID number EXACTLY as printed
- PAN format: ABCDE1234F
- Aadhaar format: XXXX XXXX XXXX (12 digits)
"""
            
            response = self.gemini.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            
            result_text = response.text.strip()
            
            # Clean JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            
            # Map document type
            doc_type_map = {
                "pan_card": IDDocumentType.PAN_CARD,
                "aadhaar_card": IDDocumentType.AADHAAR_CARD,
                "driving_license": IDDocumentType.DRIVING_LICENSE,
                "voter_id": IDDocumentType.VOTER_ID,
                "passport": IDDocumentType.PASSPORT,
            }
            doc_type = doc_type_map.get(data.get("document_type", "").lower(), IDDocumentType.UNKNOWN)
            
            return IDDocumentInfo(
                document_type=doc_type,
                full_name=data.get("full_name", "Unknown"),
                date_of_birth=data.get("date_of_birth"),
                id_number=data.get("id_number", ""),
                address=data.get("address"),
                gender=data.get("gender"),
                father_name=data.get("father_name"),
                issue_date=data.get("issue_date"),
                expiry_date=data.get("expiry_date"),
                document_language=data.get("document_language", "Unknown"),
                confidence_score=float(data.get("confidence", 0.5)),
                raw_extracted_text=data.get("raw_text", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Failed to parse ID document: {e}")
        except Exception as e:
            logger.error(f"ID document parsing error: {e}", exc_info=True)
            raise
    
    def validate_age_requirement(
        self,
        id_info: IDDocumentInfo,
        role: str
    ) -> Dict[str, Any]:
        """
        Validate age requirement for a role.
        Age requirements are NOT exposed to the user.
        
        Returns:
            {
                "valid": bool,
                "age": int or None,
                "error": str or None (generic error, not revealing min age)
            }
        """
        min_age = self.AGE_REQUIREMENTS.get(role)
        
        if not min_age:
            return {"valid": True, "age": None, "error": None}
        
        age = id_info.calculate_age()
        
        if age is None:
            return {
                "valid": False,
                "age": None,
                "error": "Could not determine age from document. Please provide a clearer document."
            }
        
        if age < min_age:
            # Generic error - does NOT reveal the minimum age requirement
            return {
                "valid": False,
                "age": age,
                "error": "You are not eligible for this role based on age requirements."
            }
        
        return {
            "valid": True,
            "age": age,
            "error": None
        }
    
    def validate_id_format(self, id_info: IDDocumentInfo) -> Dict[str, Any]:
        """
        Validate ID number format.
        """
        import re
        
        id_number = id_info.id_number.replace(" ", "").upper()
        
        validations = {
            IDDocumentType.PAN_CARD: {
                "pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]$",
                "name": "PAN Card",
                "example": "ABCDE1234F"
            },
            IDDocumentType.AADHAAR_CARD: {
                "pattern": r"^[0-9]{12}$",
                "name": "Aadhaar Card",
                "example": "XXXX XXXX XXXX"
            },
            IDDocumentType.DRIVING_LICENSE: {
                # DL format varies by state, basic check
                "pattern": r"^[A-Z]{2}[0-9]{2}[0-9A-Z]+$",
                "name": "Driving License",
                "example": "MH01 2020 0012345"
            }
        }
        
        validation = validations.get(id_info.document_type)
        
        if not validation:
            return {"valid": True, "message": "Document type not validated"}
        
        if re.match(validation["pattern"], id_number):
            return {
                "valid": True,
                "message": f"{validation['name']} format is valid"
            }
        else:
            return {
                "valid": False,
                "message": f"Invalid {validation['name']} format. Expected format: {validation['example']}"
            }
    
    def get_summary(self, id_info: IDDocumentInfo) -> str:
        """Generate human-readable summary"""
        age = id_info.calculate_age()
        age_str = f"{age} years" if age else "Unknown"
        
        return f"""
🪪 **ID Document Summary**

**Type:** {id_info.document_type.value.replace('_', ' ').title()}
**Name:** {id_info.full_name}
**ID Number:** {id_info.id_number}
**Date of Birth:** {id_info.date_of_birth or 'Not found'}
**Age:** {age_str}
**Gender:** {id_info.gender or 'Not found'}
**Address:** {id_info.address or 'Not found'}
**Language:** {id_info.document_language}
**Confidence:** {id_info.confidence_score:.0%}
""".strip()


# Global instance
id_verification_service = IDDocumentVerificationService()


# Convenience functions
async def parse_id_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Parse ID document and return structured info"""
    id_info = await id_verification_service.parse_id_document(file_bytes, filename)
    
    return {
        "document_type": id_info.document_type.value,
        "full_name": id_info.full_name,
        "date_of_birth": id_info.date_of_birth,
        "id_number": id_info.id_number,
        "age": id_info.calculate_age(),
        "address": id_info.address,
        "gender": id_info.gender,
        "confidence_score": id_info.confidence_score,
        "summary": id_verification_service.get_summary(id_info)
    }


async def validate_asha_registration(
    file_bytes: bytes,
    filename: str
) -> Dict[str, Any]:
    """
    Validate ID document for ASHA worker registration.
    
    Checks:
    1. Document is valid and parseable
    2. Age is at least 21 (hidden requirement)
    3. ID format is valid
    
    Returns:
        {
            "eligible": bool,
            "id_info": {...},
            "error": str or None
        }
    """
    try:
        id_info = await id_verification_service.parse_id_document(file_bytes, filename)
        
        # Validate age (hidden requirement)
        age_result = id_verification_service.validate_age_requirement(id_info, "ASHA_WORKER")
        
        if not age_result["valid"]:
            return {
                "eligible": False,
                "id_info": None,
                "error": age_result["error"]
            }
        
        # Validate ID format
        format_result = id_verification_service.validate_id_format(id_info)
        
        return {
            "eligible": True,
            "id_info": {
                "document_type": id_info.document_type.value,
                "full_name": id_info.full_name,
                "id_number": id_info.id_number,
                "date_of_birth": id_info.date_of_birth,
                "age": id_info.calculate_age(),
                "address": id_info.address
            },
            "format_valid": format_result["valid"],
            "error": None
        }
        
    except Exception as e:
        logger.error(f"ASHA registration validation error: {e}")
        return {
            "eligible": False,
            "id_info": None,
            "error": f"Failed to process document: {str(e)}"
        }
