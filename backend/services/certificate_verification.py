"""
Doctor Certificate Verification Service
Parses medical certificates in ANY language and verifies against public registries

Legal Sources Used:
- NMC (National Medical Commission) - Public Indian Medical Register
- State Medical Councils - Public registries
"""

import os
import io
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Gemini for multilingual parsing
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


class VerificationStatus(Enum):
    VERIFIED = "verified"
    PENDING = "pending_manual_review"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class CertificateInfo:
    """Extracted information from a certificate"""
    doctor_name: str
    registration_number: str
    council_name: str  # e.g., "Maharashtra Medical Council"
    qualification: str  # e.g., "MBBS", "MD"
    university: str
    year_of_registration: Optional[str]
    valid_until: Optional[str]
    specialization: Optional[str]
    document_language: str
    raw_extracted_text: str
    confidence_score: float


@dataclass
class VerificationResult:
    """Result of verification against public registry"""
    status: VerificationStatus
    certificate_info: CertificateInfo
    registry_match: Optional[Dict]  # Data from NMC/State registry if found
    verification_source: str  # "NMC" / "State Medical Council" / "Manual"
    verified_at: str
    notes: List[str]


class CertificateVerificationService:
    """
    Service for parsing and verifying medical certificates.
    
    Supports:
    - Multilingual certificate parsing (Hindi, Tamil, Marathi, English, etc.)
    - NMC (National Medical Commission) verification
    - State Medical Council verification
    """
    
    # State Medical Council codes and URLs
    STATE_COUNCILS = {
        "MH": {"name": "Maharashtra Medical Council", "code": "MH"},
        "KA": {"name": "Karnataka Medical Council", "code": "KA"},
        "TN": {"name": "Tamil Nadu Medical Council", "code": "TN"},
        "DL": {"name": "Delhi Medical Council", "code": "DL"},
        "GJ": {"name": "Gujarat Medical Council", "code": "GJ"},
        "RJ": {"name": "Rajasthan Medical Council", "code": "RJ"},
        "UP": {"name": "Uttar Pradesh Medical Council", "code": "UP"},
        "WB": {"name": "West Bengal Medical Council", "code": "WB"},
        "AP": {"name": "Andhra Pradesh Medical Council", "code": "AP"},
        "TS": {"name": "Telangana State Medical Council", "code": "TS"},
        "KL": {"name": "Travancore Cochin Medical Council", "code": "KL"},
        "MP": {"name": "Madhya Pradesh Medical Council", "code": "MP"},
        # Add more as needed
    }
    
    # NMC Public Registry URL (for reference - actual verification is manual)
    NMC_REGISTRY_URL = "https://www.nmc.org.in/information-desk/indian-medical-register/"
    
    def __init__(self):
        self.gemini = gemini_client
        self.model_name = "gemini-2.5-flash"
    
    async def parse_certificate(
        self,
        file_bytes: bytes,
        filename: str
    ) -> CertificateInfo:
        """
        Parse a certificate image/PDF in ANY language.
        Uses Gemini Vision to extract structured information.
        """
        if not self.gemini:
            raise ValueError("Gemini API not configured. Set GEMINI_API_KEY.")
        
        logger.info(f"📜 Parsing certificate: {filename}")
        
        try:
            # Convert bytes to PIL Image
            if Image is None:
                raise ImportError("PIL not installed")
            
            # Check if this is a PDF by magic bytes or filename
            is_pdf = filename.lower().endswith('.pdf') or file_bytes.startswith(b'%PDF')
             
            if is_pdf:
                try:
                    import fitz  # PyMuPDF
                    # Open the PDF with PyMuPDF
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    if doc.page_count == 0:
                        raise ValueError("PDF is empty")
                    # Render the first page to an image
                    page = doc.load_page(0)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))
                except ImportError:
                    logger.warning("PyMuPDF not found. Falling back to treating as generic image, which may fail.")
                    image = Image.open(io.BytesIO(file_bytes))
            else:
                image = Image.open(io.BytesIO(file_bytes))
            
            # Multilingual parsing prompt
            prompt = """You are an expert document parser. Analyze this medical/doctor certificate image.
The document may be in ANY language (Hindi, Tamil, Marathi, Bengali, English, French, etc.).

It is likely a Medical Council Registration Certificate (State or National).
Common format: Header -> Table of details -> Footer.

Look for "Name", "Name of the Doctor", "Certified that", or similar indicators for the name.
If the name is in a table row labeled "Name", extract it.

Extract ALL information and return in this EXACT JSON format:
{
    "doctor_name": "Full name of the doctor (e.g. 'GANDHI SANJAY', 'Dr. Aditi Sharma')",
    "registration_number": "Medical registration number (e.g., MH/12345, 26001, 2020/03/1234)",
    "council_name": "Name of medical council (e.g., Maharashtra Medical Council, Medical Council of India)",
    "council_state_code": "2-letter state code if Indian (MH, KA, TN, etc.) or country code",
    "qualification": "Primary qualification (MBBS, MD, MS, etc.)",
    "university": "University name where they graduated",
    "year_of_registration": "Year when registered (YYYY format)",
    "valid_until": "Expiry date if mentioned (YYYY-MM-DD format) or null",
    "specialization": "Medical specialization if mentioned or null",
    "document_language": "Primary language of the document",
    "raw_text": "Key text extracted from the certificate (especially name and reg no)",
    "confidence": "0.0 to 1.0 confidence score in extraction accuracy"
}

IMPORTANT:
- Return ONLY valid JSON
- If the name is written as 'Patil Virendra' or 'Surname Name', extract it as is or normalize to 'First Last' if clear.
- Be very careful with names in ALL CAPS.
- If a field is not visible, use null.
- Translate names to English but keep registration numbers exactly as written.
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
            
            return CertificateInfo(
                doctor_name=data.get("doctor_name", "Unknown"),
                registration_number=data.get("registration_number", ""),
                council_name=data.get("council_name", ""),
                qualification=data.get("qualification", ""),
                university=data.get("university", ""),
                year_of_registration=data.get("year_of_registration"),
                valid_until=data.get("valid_until"),
                specialization=data.get("specialization"),
                document_language=data.get("document_language", "Unknown"),
                raw_extracted_text=data.get("raw_text", ""),
                confidence_score=float(data.get("confidence", 0.5))
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Failed to parse certificate: {e}")
        except Exception as e:
            logger.error(f"Certificate parsing error: {e}", exc_info=True)
            raise
    
    async def verify_with_nmc(
        self,
        registration_number: str,
        doctor_name: str,
        council_name: str = None
    ) -> Dict[str, Any]:
        """
        Verify doctor registration against NMC public registry.
        
        NOTE: NMC doesn't have a public API, so this returns a 
        verification guide for manual checking. In production,
        you could implement web automation or partner with NMC.
        """
        logger.info(f"🔍 Verifying {doctor_name} (Reg: {registration_number})")
        
        # Clean registration number
        reg_clean = registration_number.strip().upper()
        
        # Determine likely state from registration number format
        state_code = None
        for code in self.STATE_COUNCILS.keys():
            if reg_clean.startswith(code):
                state_code = code
                break
        
        verification_guide = {
            "registration_number": reg_clean,
            "doctor_name": doctor_name,
            "council": council_name,
            "state_code": state_code,
            "verification_url": self.NMC_REGISTRY_URL,
            "manual_steps": [
                f"1. Go to {self.NMC_REGISTRY_URL}",
                f"2. Enter Registration Number: {reg_clean}",
                f"3. Enter Name: {doctor_name}",
                "4. Click Search",
                "5. Verify the returned details match the certificate"
            ]
        }
        
        # Try to auto-verify using web search (legal - public data)
        try:
            is_found, registry_data = await self._search_public_registry(
                reg_clean, doctor_name, state_code
            )
            
            if is_found:
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "registry_data": registry_data,
                    "source": "NMC Public Registry",
                    "verification_guide": verification_guide
                }
        except Exception as e:
            logger.warning(f"Auto-verification failed: {e}")
        
        # Return pending for manual review
        return {
            "verified": False,
            "status": "PENDING_MANUAL_REVIEW",
            "registry_data": None,
            "source": "Manual verification required",
            "verification_guide": verification_guide,
            "notes": [
                "Auto-verification not available for this registration",
                "Please manually verify using the NMC website"
            ]
        }
    
    async def _search_public_registry(
        self,
        registration_number: str,
        doctor_name: str,
        state_code: str = None
    ) -> tuple:
        """
        Search public registry for doctor information.
        Returns (found: bool, data: dict)
        """
        # This is a placeholder for actual registry lookup
        # In production, you would:
        # 1. Use official API if available
        # 2. Use authorized web automation
        # 3. Partner with NMC for bulk verification
        
        # For now, return not found to trigger manual review
        return (False, None)
    
    async def verify_certificate(
        self,
        file_bytes: bytes,
        filename: str
    ) -> VerificationResult:
        """
        Complete certificate verification flow:
        1. Parse certificate (multilingual)
        2. Extract registration details
        3. Verify against public registry
        4. Return verification result
        """
        logger.info(f"📋 Starting certificate verification: {filename}")
        
        try:
            # Step 1: Parse certificate
            cert_info = await self.parse_certificate(file_bytes, filename)
            logger.info(f"✅ Parsed: {cert_info.doctor_name} ({cert_info.registration_number})")
            
            # Step 2: Validate extracted info
            notes = []
            
            if not cert_info.registration_number:
                notes.append("Registration number not found on certificate")
                return VerificationResult(
                    status=VerificationStatus.INVALID,
                    certificate_info=cert_info,
                    registry_match=None,
                    verification_source="Certificate Parsing",
                    verified_at=datetime.now().isoformat(),
                    notes=["Registration number is required for verification"]
                )
            
            if cert_info.confidence_score < 0.5:
                notes.append("Low confidence in extraction - manual review recommended")
            
            # Step 3: Verify with NMC
            nmc_result = await self.verify_with_nmc(
                cert_info.registration_number,
                cert_info.doctor_name,
                cert_info.council_name
            )
            
            # Step 4: Determine status
            if nmc_result.get("verified"):
                status = VerificationStatus.VERIFIED
                notes.append("✅ Verified against NMC Public Registry")
            else:
                status = VerificationStatus.PENDING
                notes.append("⏳ Pending manual verification")
                notes.extend(nmc_result.get("notes", []))
            
            return VerificationResult(
                status=status,
                certificate_info=cert_info,
                registry_match=nmc_result.get("registry_data"),
                verification_source=nmc_result.get("source", "Manual"),
                verified_at=datetime.now().isoformat(),
                notes=notes
            )
            
        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            return VerificationResult(
                status=VerificationStatus.ERROR,
                certificate_info=CertificateInfo(
                    doctor_name="",
                    registration_number="",
                    council_name="",
                    qualification="",
                    university="",
                    year_of_registration=None,
                    valid_until=None,
                    specialization=None,
                    document_language="",
                    raw_extracted_text="",
                    confidence_score=0.0
                ),
                registry_match=None,
                verification_source="Error",
                verified_at=datetime.now().isoformat(),
                notes=[f"Verification failed: {str(e)}"]
            )
    
    def get_verification_summary(self, result: VerificationResult) -> str:
        """Generate human-readable verification summary"""
        cert = result.certificate_info
        
        status_emoji = {
            VerificationStatus.VERIFIED: "✅",
            VerificationStatus.PENDING: "⏳",
            VerificationStatus.NOT_FOUND: "❓",
            VerificationStatus.INVALID: "❌",
            VerificationStatus.ERROR: "⚠️"
        }
        
        summary = f"""
{status_emoji.get(result.status, "❓")} **Certificate Verification Result**

**Doctor:** {cert.doctor_name}
**Registration No:** {cert.registration_number}
**Council:** {cert.council_name}
**Qualification:** {cert.qualification}
**University:** {cert.university}

**Status:** {result.status.value.upper()}
**Verified At:** {result.verified_at[:10]}
**Source:** {result.verification_source}

**Notes:**
{chr(10).join('• ' + note for note in result.notes)}
"""
        return summary.strip()


# Global instance
certificate_verifier = CertificateVerificationService()


# Convenience functions
async def verify_doctor_certificate(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Verify a doctor certificate and return structured result.
    Use this from routes or telegram bot.
    """
    result = await certificate_verifier.verify_certificate(file_bytes, filename)
    
    return {
        "status": result.status.value,
        "doctor_name": result.certificate_info.doctor_name,
        "registration_number": result.certificate_info.registration_number,
        "council": result.certificate_info.council_name,
        "qualification": result.certificate_info.qualification,
        "university": result.certificate_info.university,
        "document_language": result.certificate_info.document_language,
        "verification_source": result.verification_source,
        "verified_at": result.verified_at,
        "notes": result.notes,
        "summary": certificate_verifier.get_verification_summary(result)
    }


async def parse_certificate_only(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Parse certificate without verification - just extract information.
    """
    cert_info = await certificate_verifier.parse_certificate(file_bytes, filename)
    
    return {
        "doctor_name": cert_info.doctor_name,
        "registration_number": cert_info.registration_number,
        "council": cert_info.council_name,
        "qualification": cert_info.qualification,
        "university": cert_info.university,
        "year_of_registration": cert_info.year_of_registration,
        "valid_until": cert_info.valid_until,
        "specialization": cert_info.specialization,
        "document_language": cert_info.document_language,
        "confidence_score": cert_info.confidence_score
    }
