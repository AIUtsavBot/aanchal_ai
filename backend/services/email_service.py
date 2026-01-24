"""
MatruRaksha AI - Email Notification Service (Resend)
Sends email alerts to ASHA workers and Doctors using Resend API
"""

import os
import logging
import httpx
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Resend API Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME = os.getenv("FROM_NAME", "MatruRaksha AI")

RESEND_API_URL = "https://api.resend.com/emails"


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> Dict:
    """
    Send an email using Resend API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (optional)
        
    Returns:
        Dict with status and message
    """
    if not RESEND_API_KEY:
        logger.warning("❌ Email not configured: RESEND_API_KEY missing")
        return {"status": "error", "error": "Resend API key not configured"}
    
    if not to_email:
        return {"status": "error", "error": "No recipient email provided"}
    
    try:
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": body_html
        }
        
        if body_text:
            payload["text"] = body_text
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(RESEND_API_URL, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ Email sent to {to_email} via Resend (ID: {result.get('id')})")
            return {"status": "sent", "to": to_email, "id": result.get("id")}
        else:
            error_msg = response.text
            logger.error(f"❌ Resend API error: {error_msg}")
            return {"status": "error", "error": error_msg}
        
    except httpx.TimeoutException:
        logger.error("❌ Resend API timeout")
        return {"status": "error", "error": "Request timeout"}
    except Exception as e:
        logger.error(f"❌ Email send failed: {e}")
        return {"status": "error", "error": str(e)}


def send_alert_email(
    to_email: str,
    recipient_name: str,
    recipient_role: str,  # "ASHA Worker" or "Doctor"
    mother_name: str,
    mother_id: str,
    mother_phone: str,
    location: str,
    alert_type: str = "emergency",
    additional_details: Optional[Dict] = None
) -> Dict:
    """
    Send a formatted alert email for emergencies or updates.
    
    Args:
        to_email: Recipient email
        recipient_name: Name of the doctor/ASHA worker
        recipient_role: "ASHA Worker" or "Doctor"
        mother_name: Name of the mother
        mother_id: ID of the mother
        mother_phone: Phone number of the mother
        location: Mother's location
        alert_type: Type of alert (emergency, update, reminder)
        additional_details: Extra information to include
    """
    now = datetime.now()
    timestamp = now.strftime("%d %B %Y at %I:%M %p")
    
    # Determine urgency styling
    if alert_type == "emergency":
        alert_badge = "🚨 URGENT"
        badge_color = "#dc2626"
        subject = f"🚨 URGENT: Alert for {mother_name} - {location}"
    else:
        alert_badge = "ℹ️ UPDATE"
        badge_color = "#2563eb"
        subject = f"ℹ️ Update: {mother_name} - {location}"
    
    # Build additional details section
    details_html = ""
    if additional_details:
        details_html = "<h3 style='color: #374151; margin-top: 20px;'>Additional Details:</h3><ul>"
        for key, value in additional_details.items():
            details_html += f"<li><strong>{key}:</strong> {value}</li>"
        details_html += "</ul>"
    
    # HTML email template
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">MatruRaksha AI</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Maternal Health Guardian System</p>
            </div>
            
            <!-- Alert Badge -->
            <div style="background-color: {badge_color}; color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 18px;">
                {alert_badge}
            </div>
            
            <!-- Main Content -->
            <div style="background-color: white; padding: 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="color: #374151; font-size: 16px;">Dear <strong>{recipient_name}</strong>,</p>
                
                <p style="color: #374151; font-size: 16px;">
                    An alert has been raised for one of your assigned patients. Please respond as soon as possible.
                </p>
                
                <!-- Mother Details Card -->
                <div style="background-color: #fdf2f8; border-left: 4px solid #ec4899; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                    <h3 style="color: #9d174d; margin: 0 0 15px 0;">Patient Information</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280; width: 40%;">👩 Name:</td>
                            <td style="padding: 8px 0; color: #111827; font-weight: bold;">{mother_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">🆔 ID:</td>
                            <td style="padding: 8px 0; color: #111827; font-family: monospace;">{mother_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">📱 Phone:</td>
                            <td style="padding: 8px 0; color: #111827;">{mother_phone or 'Not available'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">📍 Location:</td>
                            <td style="padding: 8px 0; color: #111827;">{location or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">⏰ Alert Time:</td>
                            <td style="padding: 8px 0; color: #111827;">{timestamp}</td>
                        </tr>
                    </table>
                </div>
                
                {details_html}
                
                <!-- Action Required -->
                <div style="background-color: #fef3c7; border: 1px solid #fcd34d; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="color: #92400e; margin: 0; font-weight: bold;">⚡ Action Required</p>
                    <p style="color: #92400e; margin: 10px 0 0 0;">Please contact the patient or visit at the earliest convenience.</p>
                </div>
                
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                    This is an automated message from MatruRaksha AI maternal health monitoring system.
                    Please do not reply to this email.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                <p>MatruRaksha AI - Protecting Mothers, Saving Lives</p>
                <p>© {now.year} MatruRaksha AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    body_text = f"""
MatruRaksha AI - {alert_badge}

Dear {recipient_name},

An alert has been raised for one of your assigned patients. Please respond as soon as possible.

PATIENT INFORMATION:
- Name: {mother_name}
- ID: {mother_id}
- Phone: {mother_phone or 'Not available'}
- Location: {location or 'Not specified'}
- Alert Time: {timestamp}

ACTION REQUIRED: Please contact the patient or visit at the earliest convenience.

This is an automated message from MatruRaksha AI maternal health monitoring system.
    """
    
    return send_email(to_email, subject, body_html, body_text)


def send_risk_alert_email(
    to_email: str,
    recipient_name: str,
    recipient_role: str,
    mother_name: str,
    mother_id: str,
    mother_phone: str,
    location: str,
    risk_level: str,
    risk_score: float,
    risk_factors: list = None
) -> Dict:
    """Send email alert for high-risk assessment results."""
    additional_details = {
        "Risk Level": risk_level.upper(),
        "Risk Score": f"{risk_score:.1%}" if isinstance(risk_score, float) else str(risk_score),
    }
    if risk_factors:
        additional_details["Risk Factors"] = ", ".join(risk_factors[:5])
    
    return send_alert_email(
        to_email=to_email,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        mother_name=mother_name,
        mother_id=mother_id,
        mother_phone=mother_phone,
        location=location,
        alert_type="emergency",
        additional_details=additional_details
    )
