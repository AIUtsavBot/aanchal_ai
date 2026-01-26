"""
Notification Background Tasks
Email, SMS, and push notification tasks
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_email_async(
    self,
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> Dict[str, Any]:
    """
    Background task for sending emails
    
    Args:
        to_email: Recipient email
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
    
    Returns:
        Send result
    """
    task_id = self.request.id
    logger.info(f"📧 Sending email to {to_email} (task: {task_id})")
    
    try:
        # Import email service
        from services.email_service import send_email
        
        result = send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        logger.info(f"✅ Email sent to {to_email}")
        return {"status": "sent", "to": to_email, "task_id": task_id}
        
    except Exception as e:
        logger.error(f"❌ Email failed to {to_email}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {"status": "failed", "error": str(e), "to": to_email}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_async(
    self,
    phone_number: str,
    message: str
) -> Dict[str, Any]:
    """
    Background task for sending SMS
    
    Args:
        phone_number: Recipient phone number
        message: SMS message
    
    Returns:
        Send result
    """
    task_id = self.request.id
    logger.info(f"📱 Sending SMS to {phone_number} (task: {task_id})")
    
    try:
        # Import SMS service
        from services.sms_service import send_sms
        
        result = send_sms(phone_number=phone_number, message=message)
        
        logger.info(f"✅ SMS sent to {phone_number}")
        return {"status": "sent", "to": phone_number, "task_id": task_id}
        
    except Exception as e:
        logger.error(f"❌ SMS failed to {phone_number}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {"status": "failed", "error": str(e), "to": phone_number}


@shared_task(bind=True, max_retries=2)
def send_telegram_async(
    self,
    chat_id: str,
    message: str,
    parse_mode: str = "HTML"
) -> Dict[str, Any]:
    """
    Background task for sending Telegram messages
    
    Args:
        chat_id: Telegram chat ID
        message: Message content
        parse_mode: Message parse mode
    
    Returns:
        Send result
    """
    task_id = self.request.id
    logger.info(f"📬 Sending Telegram to {chat_id} (task: {task_id})")
    
    try:
        import requests
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return {"status": "failed", "error": "Bot token not configured"}
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }, timeout=10)
        
        if response.ok:
            logger.info(f"✅ Telegram sent to {chat_id}")
            return {"status": "sent", "to": chat_id}
        else:
            raise Exception(f"Telegram API error: {response.text}")
        
    except Exception as e:
        logger.error(f"❌ Telegram failed to {chat_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {"status": "failed", "error": str(e), "to": chat_id}


@shared_task(bind=True, max_retries=3)
def send_high_risk_alert_async(
    self,
    mother_id: str,
    risk_level: str,
    risk_factors: List[str]
) -> Dict[str, Any]:
    """
    Send alert for high-risk mothers to doctor and ASHA worker
    
    Args:
        mother_id: Mother's ID
        risk_level: Risk level (HIGH, MODERATE, LOW)
        risk_factors: List of risk factors
    
    Returns:
        Alert result
    """
    task_id = self.request.id
    logger.info(f"🚨 Sending high-risk alert for mother {mother_id} (task: {task_id})")
    
    try:
        from supabase import create_client
        
        supabase = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", "")
        )
        
        # Get mother details with assigned healthcare workers
        mother_result = supabase.table("mothers").select(
            "*, doctors:doctor_id(*), asha_workers:asha_worker_id(*)"
        ).eq("id", mother_id).single().execute()
        
        mother = mother_result.data
        if not mother:
            return {"status": "failed", "error": "Mother not found"}
        
        # Build alert message
        alert_message = f"""
🚨 <b>HIGH RISK ALERT</b> 🚨

<b>Patient:</b> {mother.get('name', 'Unknown')}
<b>Risk Level:</b> {risk_level}
<b>Risk Factors:</b>
{chr(10).join(f"• {rf}" for rf in risk_factors)}

<b>Contact:</b> {mother.get('phone', 'N/A')}
<b>Location:</b> {mother.get('location', 'N/A')}

Please take immediate action.
        """.strip()
        
        results = []
        
        # Send to doctor
        doctor = mother.get("doctors")
        if doctor and doctor.get("email"):
            send_email_async.delay(
                to_email=doctor["email"],
                subject=f"🚨 High Risk Alert: {mother.get('name')}",
                body=alert_message.replace("<b>", "").replace("</b>", "")
            )
            results.append({"type": "email", "to": doctor["email"]})
        
        # Send to ASHA worker
        asha = mother.get("asha_workers")
        if asha and asha.get("phone"):
            send_sms_async.delay(
                phone_number=asha["phone"],
                message=f"HIGH RISK ALERT: {mother.get('name')} - {', '.join(risk_factors[:3])}. Contact immediately."
            )
            results.append({"type": "sms", "to": asha["phone"]})
        
        logger.info(f"✅ High-risk alerts sent for mother {mother_id}")
        
        return {
            "status": "success",
            "mother_id": mother_id,
            "notifications": results
        }
        
    except Exception as e:
        logger.error(f"❌ High-risk alert failed: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task
def check_pending_reminders() -> Dict[str, Any]:
    """Periodic task to check and send pending reminders"""
    logger.info("⏰ Checking pending reminders...")
    
    try:
        from supabase import create_client
        
        supabase = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", "")
        )
        
        # Get upcoming appointments (next 24 hours)
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        today = datetime.utcnow().isoformat()
        
        # Check for upcoming visits
        visits_result = supabase.table("visits").select(
            "*, mothers:mother_id(name, phone)"
        ).gte("scheduled_date", today).lte("scheduled_date", tomorrow).execute()
        
        visits = visits_result.data or []
        sent_count = 0
        
        for visit in visits:
            mother = visit.get("mothers", {})
            if mother.get("phone"):
                send_sms_async.delay(
                    phone_number=mother["phone"],
                    message=f"Reminder: You have a scheduled visit tomorrow. Please be available."
                )
                sent_count += 1
        
        logger.info(f"✅ Sent {sent_count} reminders")
        
        return {"status": "success", "reminders_sent": sent_count}
        
    except Exception as e:
        logger.error(f"❌ Reminder check failed: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def send_vaccination_reminder_async(
    self,
    child_id: str,
    vaccination_name: str,
    due_date: str
) -> Dict[str, Any]:
    """
    Send vaccination reminder to mother
    
    Args:
        child_id: Child's ID
        vaccination_name: Name of vaccination
        due_date: Due date string
    
    Returns:
        Reminder result
    """
    task_id = self.request.id
    logger.info(f"💉 Sending vaccination reminder for child {child_id} (task: {task_id})")
    
    try:
        from supabase import create_client
        
        supabase = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", "")
        )
        
        # Get child with mother info
        child_result = supabase.table("children").select(
            "*, mothers:mother_id(name, phone)"
        ).eq("id", child_id).single().execute()
        
        child = child_result.data
        if not child:
            return {"status": "failed", "error": "Child not found"}
        
        mother = child.get("mothers", {})
        
        message = f"""
Vaccination Reminder 💉

Dear {mother.get('name', 'Parent')},
Your child {child.get('name', '')} is due for {vaccination_name} vaccination on {due_date}.

Please visit your nearest health center.
        """.strip()
        
        if mother.get("phone"):
            send_sms_async.delay(phone_number=mother["phone"], message=message)
            logger.info(f"✅ Vaccination reminder sent for child {child_id}")
            return {"status": "sent", "child_id": child_id}
        
        return {"status": "no_phone", "child_id": child_id}
        
    except Exception as e:
        logger.error(f"❌ Vaccination reminder failed: {e}")
        return {"status": "failed", "error": str(e)}
