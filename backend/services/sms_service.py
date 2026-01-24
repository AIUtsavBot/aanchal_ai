"""
Fast2SMS Service for MatruRaksha AI
Free SMS notifications for ASHA workers, doctors, and mothers

NOTE: All API keys and credentials must be set in .env file:
- FAST2SMS_API_KEY: Your Fast2SMS API key
- TWILIO_ACCOUNT_SID: Twilio account SID (optional, legacy)
- TWILIO_AUTH_TOKEN: Twilio auth token (optional, legacy)
- TWILIO_FROM_NUMBER: Twilio phone number (optional, legacy)
"""
import os
import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Fast2SMS Configuration - API key loaded from environment
# Get your free API key at https://www.fast2sms.com/
FAST2SMS_API_KEY = (os.getenv("FAST2SMS_API_KEY") or "").strip()
FAST2SMS_API_URL = "https://www.fast2sms.com/dev/bulkV2"

# Legacy Twilio config (optional, kept for backward compatibility)
# All credentials must be in .env file - never hardcode
TWILIO_ACCOUNT_SID = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
TWILIO_AUTH_TOKEN = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
TWILIO_FROM_NUMBER = (os.getenv("TWILIO_FROM_NUMBER") or "").strip()



def send_sms(to_number: str, body: str) -> Dict[str, Optional[str]]:
    """
    Send SMS using Fast2SMS API (free tier for India).
    Falls back to Twilio if Fast2SMS is not configured.
    
    Args:
        to_number: Recipient phone number (10 digits for India, or with country code)
        body: Message content (max 160 chars for single SMS)
    
    Returns:
        Dict with status and details
    """
    # Try Fast2SMS first (free)
    if FAST2SMS_API_KEY:
        return _send_via_fast2sms(to_number, body)
    
    # Fallback to Twilio if configured
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        return _send_via_twilio(to_number, body)
    
    logger.warning("⚠️ SMS service not configured. Set FAST2SMS_API_KEY in .env")
    return {"status": "error", "error": "SMS service not configured"}


def _normalize_indian_number(phone: str) -> str:
    """
    Normalize phone number to 10-digit Indian format.
    Removes country code (+91, 91) and spaces/dashes.
    """
    # Remove common prefixes and non-digit characters
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Remove country code if present
    if cleaned.startswith('91') and len(cleaned) > 10:
        cleaned = cleaned[2:]
    elif cleaned.startswith('0') and len(cleaned) > 10:
        cleaned = cleaned[1:]
    
    return cleaned


def _send_via_fast2sms(to_number: str, body: str) -> Dict[str, Optional[str]]:
    """
    Send SMS using Fast2SMS Quick SMS API.
    
    Fast2SMS Quick SMS Route:
    - Free promotional SMS
    - Works 9 AM to 9 PM for promotional content
    - Transactional route available with DLT registration
    """
    try:
        # Normalize phone number for India
        phone = _normalize_indian_number(to_number)
        
        if len(phone) != 10:
            logger.error(f"❌ Invalid phone number format: {to_number} -> {phone}")
            return {"status": "error", "error": f"Invalid phone number: {phone}"}
        
        # Fast2SMS Quick SMS API parameters
        headers = {
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "route": "q",  # Quick SMS route (free)
            "message": body,
            "language": "english",
            "flash": 0,
            "numbers": phone
        }
        
        logger.info(f"📤 Sending SMS via Fast2SMS to {phone[:4]}****")
        
        response = requests.post(
            FAST2SMS_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("return"):
            request_id = result.get("request_id", "")
            logger.info(f"✅ SMS sent successfully! Request ID: {request_id}")
            return {
                "status": "sent",
                "provider": "fast2sms",
                "request_id": request_id,
                "message": result.get("message", "SMS sent")
            }
        else:
            error_msg = result.get("message", response.text)
            logger.error(f"❌ Fast2SMS error: {error_msg}")
            return {"status": "error", "provider": "fast2sms", "error": error_msg}
            
    except requests.Timeout:
        logger.error("❌ Fast2SMS request timed out")
        return {"status": "error", "provider": "fast2sms", "error": "Request timeout"}
    except requests.RequestException as e:
        logger.error(f"❌ Fast2SMS request failed: {str(e)}")
        return {"status": "error", "provider": "fast2sms", "error": str(e)}
    except Exception as e:
        logger.error(f"❌ Unexpected error sending SMS: {str(e)}")
        return {"status": "error", "error": str(e)}


def _send_via_twilio(to_number: str, body: str) -> Dict[str, Optional[str]]:
    """
    Legacy Twilio SMS sending (paid, kept for backward compatibility).
    """
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        data = {"To": to_number, "From": TWILIO_FROM_NUMBER, "Body": body}
        
        resp = requests.post(
            url, 
            data=data, 
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), 
            timeout=10
        )
        
        if resp.status_code == 201:
            sid = resp.json().get("sid")
            logger.info(f"✅ SMS sent via Twilio! SID: {sid}")
            return {"status": "sent", "provider": "twilio", "sid": sid}
        
        logger.error(f"❌ Twilio error: {resp.text}")
        return {"status": "error", "provider": "twilio", "error": resp.text}
        
    except Exception as e:
        logger.error(f"❌ Twilio exception: {str(e)}")
        return {"status": "error", "provider": "twilio", "error": str(e)}


def check_sms_balance() -> Dict[str, any]:
    """
    Check Fast2SMS wallet balance.
    """
    if not FAST2SMS_API_KEY:
        return {"status": "error", "error": "Fast2SMS not configured"}
    
    try:
        url = f"https://www.fast2sms.com/dev/wallet?authorization={FAST2SMS_API_KEY}"
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get("return"):
            return {
                "status": "success",
                "balance": result.get("wallet"),
                "currency": "INR"
            }
        return {"status": "error", "error": result.get("message", "Unknown error")}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


def send_alert_sms(to_number: str, mother_name: str, location: str, alert_type: str = "emergency") -> Dict:
    """
    Send formatted alert SMS for emergencies.
    
    Args:
        to_number: ASHA worker or doctor phone number
        mother_name: Name of the mother
        location: Location/address
        alert_type: Type of alert (emergency, appointment, reminder)
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    if alert_type == "emergency":
        message = f"🚨 ALERT: {mother_name} needs immediate attention. Location: {location}. Time: {timestamp}. Please respond urgently."
    elif alert_type == "appointment":
        message = f"📅 Reminder: Appointment for {mother_name} at {location}. Time: {timestamp}."
    else:
        message = f"ℹ️ MatruRaksha: Update for {mother_name}. Location: {location}. Time: {timestamp}."
    
    return send_sms(to_number, message)
