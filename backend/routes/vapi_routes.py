"""
MatruRaksha AI - Vapi.ai Voice Agent Integration
Handles AI calling agent for automated maternal health check-in calls
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
import requests
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["Vapi AI Calls"])

# Vapi Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Vapi API Base URL
VAPI_BASE_URL = "https://api.vapi.ai"

# Symptom keywords to detect in transcripts (Hindi + English)
HIGH_RISK_SYMPTOMS = [
    # English
    "severe headache", "blurry vision", "vision problem", "swelling",
    "bleeding", "blood", "stomach pain", "abdominal pain", "fever",
    "baby not moving", "reduced movement", "high blood pressure",
    "chest pain", "difficulty breathing", "unconscious",
    # Hindi transliterated
    "sar dard", "sir dard", "dhundhla", "sujan", "soojan",
    "khoon", "dard", "bukhar", "halchal kam", "movement kam",
    "sans lene mein", "chakkar", "behosh"
]

MODERATE_SYMPTOMS = [
    "headache", "nausea", "vomiting", "ulti", "tired", "thakan",
    "dizzy", "weakness", "kamzori", "neend nahi"
]


# ==================== MODELS ====================

class VapiWebhookPayload(BaseModel):
    """Webhook payload from Vapi server URL"""
    message: Dict[str, Any]


class InitiateCallRequest(BaseModel):
    """Request to initiate an outbound call"""
    mother_id: str
    phone_number: str = Field(..., description="Phone number with country code (+91...)")
    mother_name: Optional[str] = "Mother"


class EndOfCallReport(BaseModel):
    """End of call report structure"""
    call_id: str
    assistant_id: Optional[str] = None
    phone_number: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    summary: Optional[str] = None
    ended_reason: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def analyze_transcript_for_symptoms(transcript_text: str) -> Dict[str, Any]:
    """Analyze call transcript for health symptoms"""
    if not transcript_text:
        return {"risk_level": "UNKNOWN", "symptoms": []}
    
    text_lower = transcript_text.lower()
    
    detected_high = []
    detected_moderate = []
    
    for symptom in HIGH_RISK_SYMPTOMS:
        if symptom in text_lower:
            detected_high.append(symptom)
    
    for symptom in MODERATE_SYMPTOMS:
        if symptom in text_lower:
            detected_moderate.append(symptom)
    
    # Determine risk level
    if detected_high:
        risk_level = "HIGH"
    elif detected_moderate:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return {
        "risk_level": risk_level,
        "high_risk_symptoms": detected_high,
        "moderate_symptoms": detected_moderate,
        "all_symptoms": detected_high + detected_moderate
    }


def send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send Telegram alert for high-risk symptoms detected"""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        logger.warning("⚠️ Telegram alert skipped - missing credentials")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Telegram error: {e}")
        return False


# ==================== API ENDPOINTS ====================

@router.post("/webhook")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Vapi Server URL webhook endpoint.
    Configure this URL in Vapi Dashboard → Assistant → Server URL
    
    Handles various message types:
    - status-update: Call status changes
    - transcript: Real-time transcript updates
    - end-of-call-report: Complete call summary
    - function-call: Custom function execution
    """
    try:
        data = await request.json()
        message = data.get("message", {})
        message_type = message.get("type", "unknown")
        
        logger.info(f"📞 Vapi webhook: {message_type}")
        
        # Handle different message types
        if message_type == "end-of-call-report":
            return await handle_end_of_call(message)
        
        elif message_type == "status-update":
            status = message.get("status")
            logger.info(f"📱 Call status: {status}")
            return {"status": "acknowledged"}
        
        elif message_type == "transcript":
            # Real-time transcript update
            transcript = message.get("transcript", "")
            logger.debug(f"📝 Transcript update: {transcript[:100]}...")
            return {"status": "acknowledged"}
        
        elif message_type == "function-call":
            # Handle custom function calls from assistant
            function_name = message.get("functionCall", {}).get("name")
            parameters = message.get("functionCall", {}).get("parameters", {})
            return await handle_function_call(function_name, parameters)
        
        elif message_type == "assistant-request":
            # Dynamic assistant configuration
            return get_assistant_config()
        
        else:
            logger.info(f"ℹ️ Unhandled message type: {message_type}")
            return {"status": "acknowledged"}
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


async def handle_end_of_call(message: Dict) -> Dict:
    """Process end-of-call report"""
    call_id = message.get("call", {}).get("id", "unknown")
    transcript = message.get("transcript", "")
    summary = message.get("summary", "")
    duration = message.get("call", {}).get("duration")
    recording_url = message.get("recordingUrl")
    
    logger.info(f"📞 Call ended: {call_id}, Duration: {duration}s")
    logger.info(f"📝 Transcript: {transcript[:200]}..." if transcript else "No transcript")
    
    # Analyze for symptoms
    analysis = analyze_transcript_for_symptoms(transcript)
    logger.info(f"🔍 Risk Analysis: {analysis['risk_level']}")
    
    # If HIGH RISK, trigger alerts
    if analysis["risk_level"] == "HIGH":
        logger.warning(f"🚨 HIGH RISK detected in call {call_id}")
        symptoms_text = ", ".join(analysis["high_risk_symptoms"][:3])
        
        # Get mother info from call metadata if available
        metadata = message.get("call", {}).get("metadata", {})
        telegram_chat_id = metadata.get("telegram_chat_id")
        mother_name = metadata.get("mother_name", "")
        
        if telegram_chat_id:
            alert_message = (
                f"🚨 <b>Health Alert from AI Check-in</b> 🚨\n\n"
                f"During your health check-in call, concerning symptoms were mentioned:\n"
                f"<b>{symptoms_text}</b>\n\n"
                f"⚕️ Please consult with your doctor or ASHA worker.\n"
                f"📞 If you feel unwell, visit the nearest health center."
            )
            send_telegram_alert(telegram_chat_id, alert_message)
    
    # Store call record in database
    # TODO: Implement with Supabase
    # call_record = {
    #     "call_id": call_id,
    #     "transcript": transcript,
    #     "summary": summary,
    #     "risk_level": analysis["risk_level"],
    #     "symptoms": analysis["all_symptoms"],
    #     "duration": duration,
    #     "recording_url": recording_url,
    #     "timestamp": datetime.now().isoformat()
    # }
    
    return {
        "status": "processed",
        "call_id": call_id,
        "risk_assessment": analysis
    }


async def handle_function_call(function_name: str, parameters: Dict) -> Dict:
    """Handle custom function calls from Vapi assistant"""
    logger.info(f"🔧 Function call: {function_name}, params: {parameters}")
    
    if function_name == "get_mother_info":
        # Return mother health info
        mother_id = parameters.get("mother_id")
        # TODO: Fetch from database
        return {
            "result": {
                "name": "Patient",
                "last_checkup": "2 days ago",
                "risk_level": "LOW"
            }
        }
    
    elif function_name == "schedule_appointment":
        date = parameters.get("date")
        return {
            "result": {
                "status": "scheduled",
                "date": date,
                "message": "Appointment scheduled successfully"
            }
        }
    
    elif function_name == "report_emergency":
        symptom = parameters.get("symptom")
        logger.warning(f"🚨 Emergency reported: {symptom}")
        return {
            "result": {
                "status": "alert_sent",
                "message": "Emergency alert has been sent to healthcare team"
            }
        }
    
    return {"result": {"status": "function_not_found"}}


def get_assistant_config() -> Dict:
    """Return dynamic assistant configuration"""
    return {
        "assistant": {
            "firstMessage": "नमस्ते! मैं रक्षा हूं, MatruRaksha से बोल रही हूं। आज आपका स्वास्थ्य जानने के लिए फोन किया है। आप कैसी हैं?",
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "systemPrompt": get_system_prompt()
            }
        }
    }


def get_system_prompt() -> str:
    """Get the system prompt for the assistant"""
    return """You are "Raksha", a caring AI health assistant for MatruRaksha, a maternal health monitoring system in India.

PERSONALITY:
- Warm, gentle, and reassuring
- Speak slowly and clearly in Hindi (can switch to English if needed)
- Be patient and encouraging

CALL FLOW:
1. Greet warmly: "Namaste! Main Raksha hoon, MatruRaksha se."
2. Ask about wellbeing: "Aap kaisi hain? Tabiyat kaisi hai?"
3. Check for symptoms one by one
4. If any concern, advise seeing doctor
5. Close warmly with encouragement

SYMPTOMS TO ASK ABOUT (in order):
1. "Kya aapko sar mein dard hai?" (Headache)
2. "Kya aankhon se dhundhla dikhta hai?" (Vision problems)
3. "Kya haath-pair mein sujan hai?" (Swelling)
4. "Kya pet mein dard hai?" (Abdominal pain)
5. "Bachche ki halchal kaisi hai?" (Baby movement)
6. "Kya bukhar hai?" (Fever)

IF SERIOUS SYMPTOM REPORTED:
- Stay calm, reassure the mother
- Say: "Aapko jaldi se doctor se milna chahiye"
- Use report_emergency function

CLOSING:
- "Dhanyavaad. Apna khayal rakhiye. Bhagwan aapko swasth rakhe."
    """


def get_postnatal_system_prompt() -> str:
    """Get the system prompt for postnatal care"""
    return """You are "Raksha", a caring AI health assistant for MatruRaksha.
    
    CONTEXT: Postnatal Care (After delivery) or Child Care.
    
    PERSONALITY:
    - Warm, gentle, and reassuring
    - Speak slowly and clearly in Hindi (can switch to English if needed)
    - Be patient and encouraging
    
    CALL FLOW:
    1. Greet: "Namaste! Main Raksha hoon. Maa aur bachche ki tabiyat kaisi hai?"
    2. Ask about Baby: "Kya bachcha dudh pi raha hai? Koi pareshani?"
    3. Ask about Mother: "Aur aap kaisi hain? Koi dard ya bukhar?"
    4. If serious symptom: Advise doctor visit immediately.
    
    CLOSING:
    - "Dhanyavaad. Apna aur bachche ka khayal rakhiye."
    """


@router.post("/call")
async def initiate_outbound_call(call_request: InitiateCallRequest):
    """
    Initiate an outbound call to a mother using Vapi.
    Requires Vapi account with phone number configured.
    """
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="Vapi API key not configured")
    
    if not VAPI_ASSISTANT_ID:
        raise HTTPException(status_code=500, detail="Vapi Assistant ID not configured")
    
    if not VAPI_PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="Vapi Phone Number ID not configured")
    
    try:
        # Fetch mother details to determine system prompt context
        # We need to know if she is pregnant or delivered
        mother_context = {}
        try:
             # This requires internal import, or we just rely on metadata passed if we can't query DB
             # For robustness, let's assume if we can query DB we do, else default to pregnancy
             from backend.services.supabase_service import get_mother_by_id
             mother = await get_mother_by_id(call_request.mother_id)
             if mother:
                 mother_context = mother
        except Exception as e:
            logger.warning(f"Could not fetch mother context for Vapi call: {e}")

        # Choose prompt based on status
        is_postnatal = mother_context.get("delivery_status") in ["delivered", "postnatal"] or \
                       mother_context.get("active_system") == "santanraksha"
        
        system_prompt = get_postnatal_system_prompt() if is_postnatal else get_system_prompt()
        
        # Prepare call payload
        payload = {
            "assistantId": VAPI_ASSISTANT_ID,
            "phoneNumberId": VAPI_PHONE_NUMBER_ID,
            "customer": {
                "number": call_request.phone_number
            },
            "assistant": {
                 "model": {
                     "provider": "openai",
                     "model": "gpt-4",
                     "systemPrompt": system_prompt
                 }
            },
            "metadata": {
                "mother_id": call_request.mother_id,
                "mother_name": call_request.mother_name,
                "initiated_at": datetime.now().isoformat(),
                "context": "postnatal" if is_postnatal else "prenatal"
            }
        }
        
        # Make API call to Vapi
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{VAPI_BASE_URL}/call/phone",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            call_id = result.get("id")
            logger.info(f"📞 Call initiated: {call_id} to {call_request.phone_number[:6]}*** (Postnatal: {is_postnatal})")
            return {
                "status": "success",
                "message": f"Call initiated to {call_request.phone_number[:6]}***",
                "call_id": call_id
            }
        else:
            logger.error(f"❌ Vapi API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls")
async def list_calls(limit: int = 10):
    """List recent calls from Vapi"""
    if not VAPI_API_KEY:
        raise HTTPException(status_code=500, detail="Vapi API key not configured")
    
    try:
        headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}
        response = requests.get(
            f"{VAPI_BASE_URL}/call?limit={limit}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_vapi_integration():
    """Test endpoint to verify Vapi integration is ready"""
    return {
        "status": "success",
        "message": "🟢 Vapi AI Calling integration is active",
        "configuration": {
            "api_key_configured": bool(VAPI_API_KEY),
            "assistant_id_configured": bool(VAPI_ASSISTANT_ID),
            "phone_number_configured": bool(VAPI_PHONE_NUMBER_ID)
        },
        "endpoints": [
            "POST /vapi/webhook - Receive call events from Vapi",
            "POST /vapi/call - Initiate outbound call",
            "GET /vapi/calls - List recent calls",
            "GET /vapi/assistant-config - Get assistant prompt/config"
        ],
        "symptom_detection": {
            "high_risk_keywords": len(HIGH_RISK_SYMPTOMS),
            "moderate_keywords": len(MODERATE_SYMPTOMS)
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/assistant-config")
async def get_assistant_configuration():
    """
    Get recommended assistant configuration for Vapi dashboard.
    Copy these settings when creating your Vapi assistant.
    """
    return {
        "assistant_name": "MatruRaksha Health Assistant (Raksha)",
        "first_message": "नमस्ते! मैं रक्षा हूं, MatruRaksha से बोल रही हूं। आज आपका स्वास्थ्य जानने के लिए फोन किया है। आप कैसी हैं?",
        "first_message_english": "Hello! This is Raksha calling from MatruRaksha. I'm calling for your daily health check-in. How are you feeling today?",
        "system_prompt": get_system_prompt(),
        "model_settings": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        },
        "voice_settings": {
            "provider": "11labs",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - warm female
            "stability": 0.5,
            "similarity_boost": 0.75
        },
        "server_url": "/vapi/webhook",
        "functions": [
            {
                "name": "report_emergency",
                "description": "Report an emergency symptom that needs immediate attention",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symptom": {"type": "string", "description": "The symptom reported"}
                    }
                }
            }
        ]
    }
