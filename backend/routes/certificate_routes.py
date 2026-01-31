"""
Certificate Verification API Routes
Endpoints for doctor certificate verification
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificate Verification"])


@router.post("/verify")
async def verify_certificate(
    file: UploadFile = File(...),
    doctor_email: Optional[str] = Form(None)
):
    """
    Verify a doctor/medical professional certificate.
    
    Supports:
    - PDF and image files (JPG, PNG)
    - Certificates in ANY language (Hindi, Tamil, Marathi, English, French, etc.)
    
    Returns:
    - Parsed certificate information
    - Verification status against NMC/State Medical Council
    """
    try:
        from services.certificate_verification import verify_doctor_certificate
        
        # Read file bytes
        file_bytes = await file.read()
        filename = file.filename or "certificate"
        
        # Validate file type
        allowed_types = ["pdf", "jpg", "jpeg", "png", "webp"]
        file_ext = filename.lower().split(".")[-1]
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_types)}"
            )
        
        logger.info(f"📜 Verifying certificate: {filename}")
        
        # Verify certificate
        result = await verify_doctor_certificate(file_bytes, filename)
        
        return {
            "success": True,
            "verification": result
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Certificate verification service not available"
        )
    except Exception as e:
        logger.error(f"Certificate verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/parse")
async def parse_certificate(file: UploadFile = File(...)):
    """
    Parse a certificate without verification.
    Just extract information from the document.
    
    Useful for:
    - Pre-filling registration forms
    - Quick certificate review
    """
    try:
        from services.certificate_verification import parse_certificate_only
        
        file_bytes = await file.read()
        filename = file.filename or "certificate"
        
        result = await parse_certificate_only(file_bytes, filename)
        
        return {
            "success": True,
            "parsed_data": result
        }
        
    except Exception as e:
        logger.error(f"Certificate parsing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )


@router.get("/nmc-lookup")
async def nmc_lookup_guide(
    registration_number: str,
    doctor_name: Optional[str] = None
):
    """
    Get guidance for manual NMC verification.
    
    Returns step-by-step instructions for verifying a doctor
    on the official NMC website.
    """
    nmc_url = "https://www.nmc.org.in/information-desk/indian-medical-register/"
    
    return {
        "success": True,
        "verification_guide": {
            "registry_url": nmc_url,
            "registration_number": registration_number,
            "doctor_name": doctor_name,
            "steps": [
                f"1. Open the NMC registry: {nmc_url}",
                f"2. Enter Registration Number: {registration_number}",
                f"3. Enter Doctor Name: {doctor_name}" if doctor_name else "3. Enter Doctor Name",
                "4. Select State Council if known",
                "5. Click 'Search'",
                "6. Verify the returned details match the certificate"
            ],
            "note": "The NMC Indian Medical Register is the official public database for verifying registered medical practitioners in India."
        }
    }


@router.get("/state-councils")
async def list_state_councils():
    """
    List all supported State Medical Councils.
    """
    from services.certificate_verification import certificate_verifier
    
    return {
        "success": True,
        "councils": certificate_verifier.STATE_COUNCILS,
        "note": "These are the State Medical Councils that issue registration to doctors in India"
    }


# ==================== ID Document Verification (PAN/Aadhaar/DL) ====================

@router.post("/id-document/parse")
async def parse_id_document_endpoint(file: UploadFile = File(...)):
    """
    Parse an ID document (PAN Card, Aadhaar, Driving License).
    
    Supports documents in ANY language (Hindi, Tamil, etc.)
    
    Returns:
    - Document type
    - Name, DOB, ID number
    - Age calculated from DOB
    """
    try:
        from services.id_document_verification import parse_id_document
        
        file_bytes = await file.read()
        filename = file.filename or "id_document"
        
        result = await parse_id_document(file_bytes, filename)
        
        return {
            "success": True,
            "document": result
        }
        
    except Exception as e:
        logger.error(f"ID document parsing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse document: {str(e)}"
        )


@router.post("/id-document/validate-asha")
async def validate_asha_id(file: UploadFile = File(...)):
    """
    Validate ID document for ASHA worker registration.
    
    Checks:
    - Document is valid and parseable
    - Age meets eligibility requirements
    - ID format is valid
    
    Note: Age requirement is enforced but not disclosed to user.
    """
    try:
        from services.id_document_verification import validate_asha_registration
        
        file_bytes = await file.read()
        filename = file.filename or "id_document"
        
        result = await validate_asha_registration(file_bytes, filename)
        
        if not result["eligible"]:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        return {
            "success": True,
            "eligible": True,
            "id_info": result["id_info"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ASHA validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/id-document/supported-types")
async def list_supported_id_types():
    """
    List supported ID document types.
    """
    return {
        "success": True,
        "supported_types": [
            {
                "type": "pan_card",
                "name": "PAN Card",
                "format": "XXXXX0000X (10 characters)",
                "issuer": "Income Tax Department, India"
            },
            {
                "type": "aadhaar_card",
                "name": "Aadhaar Card",
                "format": "0000 0000 0000 (12 digits)",
                "issuer": "UIDAI, India"
            },
            {
                "type": "driving_license",
                "name": "Driving License",
                "format": "Varies by state",
                "issuer": "State Transport Department"
            },
            {
                "type": "voter_id",
                "name": "Voter ID (EPIC)",
                "format": "ABC0000000 (10 characters)",
                "issuer": "Election Commission of India"
            }
        ],
        "note": "Documents can be in any language - Hindi, Tamil, Marathi, etc."
    }
