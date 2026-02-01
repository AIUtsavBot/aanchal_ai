"""
Demo: ID Document Verification System for ASHA Registration
This shows how the current system works step by step.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def print_step(step_num: int, title: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step_num}: {title}")
    print(f"{'='*60}\n")


async def demo_id_verification():
    """
    Demonstrate the ID verification flow for ASHA registration.
    """
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🪪 ID VERIFICATION SYSTEM DEMO                       ║
    ║     For ASHA Worker Registration                         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # ============================================================
    print_step(1, "USER UPLOADS ID DOCUMENT")
    # ============================================================
    
    print("""
    User Action:
    ┌─────────────────────────────────────────┐
    │  📤 User uploads PAN Card / Aadhaar     │
    │     (Can be in any language)            │
    │                                         │
    │  Example: Hindi Aadhaar Card            │
    │  ┌─────────────────────────────────┐    │
    │  │ आधार - भारत सरकार              │    │
    │  │ नाम: प्रिया शर्मा               │    │
    │  │ जन्म तिथि: 15/03/2005           │    │
    │  │ आधार संख्या: 1234 5678 9012    │    │
    │  └─────────────────────────────────┘    │
    └─────────────────────────────────────────┘
    """)
    
    # ============================================================
    print_step(2, "GEMINI VISION PARSES DOCUMENT")
    # ============================================================
    
    print("""
    Backend Process (Gemini AI):
    ┌─────────────────────────────────────────┐
    │  🤖 Gemini Vision API analyzes image    │
    │                                         │
    │  Prompt: "Extract all information from  │
    │  this ID document. Document may be in   │
    │  ANY language..."                       │
    │                                         │
    │  Gemini reads Hindi text and extracts:  │
    └─────────────────────────────────────────┘
    
    Extracted JSON:
    {
        "document_type": "aadhaar_card",
        "full_name": "Priya Sharma",      # Transliterated to English
        "date_of_birth": "2005-03-15",    # Converted to YYYY-MM-DD
        "id_number": "123456789012",
        "gender": "Female",
        "address": "123 Village Road, District XYZ",
        "document_language": "Hindi",
        "confidence": 0.92
    }
    """)
    
    # ============================================================
    print_step(3, "BACKEND CALCULATES AGE (HIDDEN)")
    # ============================================================
    
    print("""
    Backend Logic (NOT visible to user):
    ┌─────────────────────────────────────────┐
    │                                         │
    │  DOB: 2005-03-15                        │
    │  Today: 2026-01-31                      │
    │                                         │
    │  Calculated Age: 20 years               │
    │                                         │
    │  ❌ ASHA Requirement: 21+ years         │
    │  ❌ User age (20) < Required age (21)   │
    │                                         │
    └─────────────────────────────────────────┘
    
    CODE THAT RUNS:
    ```python
    # Hidden age requirements
    AGE_REQUIREMENTS = {
        "ASHA_WORKER": 21,  # Not shown to user!
    }
    
    age = calculate_age(dob)  # Returns 20
    
    if age < 21:
        # Generic error - does NOT reveal min age
        return {
            "eligible": False,
            "error": "You are not eligible for this role..."
        }
    ```
    """)
    
    # ============================================================
    print_step(4, "RESPONSE TO USER")
    # ============================================================
    
    print("""
    API Response (what user sees):
    
    ❌ CASE 1: Age < 21 (Rejected)
    ┌─────────────────────────────────────────┐
    │                                         │
    │  {                                      │
    │    "success": false,                    │
    │    "error": "You are not eligible for   │
    │             this role based on age      │
    │             requirements."              │
    │  }                                      │
    │                                         │
    │  ⚠️ Notice: Error does NOT say "21+"   │
    │     User cannot guess the requirement!  │
    │                                         │
    └─────────────────────────────────────────┘
    
    ✅ CASE 2: Age >= 21 (Approved)
    ┌─────────────────────────────────────────┐
    │                                         │
    │  {                                      │
    │    "success": true,                     │
    │    "eligible": true,                    │
    │    "id_info": {                         │
    │      "full_name": "Priya Sharma",       │
    │      "id_number": "123456789012",       │
    │      "age": 25,                         │
    │      "document_type": "aadhaar_card"    │
    │    }                                    │
    │  }                                      │
    │                                         │
    └─────────────────────────────────────────┘
    """)
    
    # ============================================================
    print_step(5, "COMPLETE FLOW DIAGRAM")
    # ============================================================
    
    print("""
    ┌──────────────┐
    │  User        │
    │  uploads ID  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────────────────────────────┐
    │  POST /api/v1/certificates/id-document/      │
    │       validate-asha                          │
    └──────┬───────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────┐
    │  Gemini Vision API                           │
    │  - Reads document (any language)             │
    │  - Extracts: Name, DOB, ID Number            │
    └──────┬───────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────┐
    │  Age Validation (HIDDEN)                     │
    │  - Calculate age from DOB                    │
    │  - Check: age >= 21?                         │
    └──────┬───────────────────────────────────────┘
           │
           ├─── Age < 21 ───▶ ❌ "Not eligible" (generic error)
           │
           └─── Age >= 21 ──▶ ✅ Return ID info + proceed
    """)
    
    # ============================================================
    print("\n" + "="*60)
    print("  📡 HOW TO TEST WITH REAL DOCUMENT")
    print("="*60 + "\n")
    # ============================================================
    
    print("""
    1. Start the backend:
       cd backend
       uvicorn main:app --reload
    
    2. Send a request:
       curl -X POST http://localhost:8000/api/v1/certificates/id-document/validate-asha \\
         -F "file=@your_aadhaar.jpg"
    
    3. Or use Python:
       ```python
       import requests
       
       with open("aadhaar.jpg", "rb") as f:
           response = requests.post(
               "http://localhost:8000/api/v1/certificates/id-document/validate-asha",
               files={"file": f}
           )
           print(response.json())
       ```
    """)


if __name__ == "__main__":
    asyncio.run(demo_id_verification())
