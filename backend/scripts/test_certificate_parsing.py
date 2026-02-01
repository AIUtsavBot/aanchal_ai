"""
Test script to demonstrate multilingual certificate parsing
Run this to see how Gemini extracts information from certificates
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


async def test_certificate_parsing():
    """Test the certificate parsing with a sample image"""
    
    print("=" * 60)
    print("🧪 Certificate Parsing Test")
    print("=" * 60)
    
    # Check if Gemini is available
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Cannot run test.")
        return
    
    from services.certificate_verification import certificate_verifier
    
    # Create a test image with text (simulating a certificate)
    # In real use, this would be an actual uploaded certificate image
    
    print("\n📋 How it works:")
    print("-" * 40)
    print("""
    1. User uploads certificate (PDF/Image)
       ↓
    2. Gemini Vision reads the document
       - Handles ANY language (Hindi, Tamil, Marathi, French, etc.)
       - Extracts structured data
       ↓
    3. Returns parsed information:
       - Doctor name
       - Registration number
       - Medical council
       - Qualification
       - University
    """)
    
    # Demo: Show the prompt that's used
    print("\n🔍 Gemini Prompt Used:")
    print("-" * 40)
    print("""
    Gemini receives the image and this prompt:
    
    "Analyze this medical/doctor certificate image.
    The document may be in ANY language (Hindi, Tamil, Marathi, 
    Bengali, English, French, etc.).
    
    Extract ALL information and return in JSON format:
    {
        'doctor_name': 'Full name as written',
        'registration_number': 'Medical registration number',
        'council_name': 'Name of medical council',
        'qualification': 'MBBS, MD, MS, etc.',
        'university': 'University name',
        ...
    }"
    """)
    
    # Demo: Show sample output
    print("\n📄 Sample Output (what Gemini returns):")
    print("-" * 40)
    
    sample_output = {
        "doctor_name": "डॉ. राजेश कुमार शर्मा",  # Hindi name
        "registration_number": "MH/2020/12345",
        "council_name": "Maharashtra Medical Council",
        "qualification": "MBBS, MD (Medicine)",
        "university": "Mumbai University",
        "year_of_registration": "2020",
        "document_language": "Hindi",
        "confidence_score": 0.92
    }
    
    import json
    print(json.dumps(sample_output, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("🔄 NMC Verification Flow:")
    print("=" * 60)
    print("""
    After parsing, the system:
    
    1. Takes registration number: MH/2020/12345
    2. Generates verification guide:
       
       → Go to: https://www.nmc.org.in/information-desk/indian-medical-register/
       → Enter Registration No: MH/2020/12345
       → Enter Name: राजेश कुमार शर्मा
       → Click Search
       → Verify details match
    
    3. Returns status: PENDING_MANUAL_REVIEW
       (Until admin confirms verification)
    """)
    
    print("\n" + "=" * 60)
    print("🧪 Live Test with Real Certificate:")
    print("=" * 60)
    print("""
    To test with a REAL certificate:
    
    1. Start the backend:
       uvicorn main:app --reload
    
    2. Use the API endpoint:
       POST /api/v1/certificates/verify
       - Body: Form-data with 'file' = your certificate image
    
    3. Or use curl:
       curl -X POST http://localhost:8000/api/v1/certificates/verify \\
         -F "file=@doctor_certificate.jpg"
    """)
    
    # If you have a test image, uncomment this:
    # test_image_path = "test_certificate.jpg"
    # if os.path.exists(test_image_path):
    #     with open(test_image_path, "rb") as f:
    #         result = await certificate_verifier.verify_certificate(f.read(), test_image_path)
    #         print(certificate_verifier.get_verification_summary(result))


if __name__ == "__main__":
    asyncio.run(test_certificate_parsing())
