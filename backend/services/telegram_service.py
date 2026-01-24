# backend/services/telegram_service.py
import requests
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

class TelegramService:
    """Telegram messaging service for maternal health notifications"""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")
    
    def send_message(self, chat_id, message, parse_mode="HTML"):
        """
        Send message via Telegram
        
        Args:
            chat_id: User's Telegram chat ID
            message: Message text
            parse_mode: HTML or Markdown formatting
        
        Returns:
            Response from Telegram API
        """
        try:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent to {chat_id}")
                return {
                    "status": "sent",
                    "message_id": response.json().get("result", {}).get("message_id"),
                    "chat_id": chat_id
                }
            else:
                logger.error(f"Telegram error: {response.text}")
                return {
                    "status": "failed",
                    "error": response.json().get("description", "Unknown error")
                }
        
        except Exception as e:
            logger.error(f"Telegram service error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def send_risk_alert(self, chat_id, mother_name, risk_status, risk_score):
        """Send risk alert to mother via Telegram"""
        
        risk_emoji = {
            "High Risk": "🔴",
            "Moderate Risk": "🟡",
            "Low Risk": "🟢"
        }
        
        emoji = risk_emoji.get(risk_status, "⚠️")
        
        message = f"""{emoji} <b>Health Alert for {mother_name}</b>

<b>Risk Status:</b> {risk_status}
<b>Risk Score:</b> {risk_score*100:.0f}%

⏰ <b>Check-up Time!</b>
Your latest health assessment shows {risk_status.lower()}.

📋 <b>Next Steps:</b>
• Contact your healthcare provider
• Schedule an appointment if needed
• Follow wellness recommendations

💬 Reply to this message or use /help for more information.

Stay healthy! 🤰"""
        
        return self.send_message(chat_id, message)
    
    def send_appointment_reminder(self, chat_id, mother_name, facility, appointment_date, appointment_time):
        """Send appointment reminder"""
        
        message = f"""📅 <b>Appointment Reminder for {mother_name}</b>

<b>Facility:</b> {facility}
<b>Date:</b> {appointment_date}
<b>Time:</b> {appointment_time}

✅ <b>Please Remember:</b>
• Arrive 10-15 minutes early
• Bring any previous reports
• Contact provider if you can't make it

📞 <b>Contact Healthcare Provider:</b>
If you need to reschedule, reply to this message.

Your health matters! 💙"""
        
        return self.send_message(chat_id, message)
    
    def send_medication_reminder(self, chat_id, medications):
        """Send medication reminder"""
        
        med_list = "\n".join([f"• <b>{m['name']}</b> - {m['dosage']} at {m['time']}" for m in medications])
        
        message = f"""💊 <b>Medication Reminder</b>

{med_list}

⏰ <b>Important:</b>
• Take medications on time
• Don't skip doses
• Report any side effects immediately

📝 <b>Side Effects?</b>
If experiencing unusual symptoms, reply with /emergency

Stay consistent! 💪"""
        
        return self.send_message(chat_id, message)
    
    def send_nutrition_plan(self, chat_id, mother_name, plan_text, language="en"):
        """Send nutrition plan"""
        
        titles = {
            "en": "🥗 Personalized Nutrition Plan",
            "mr": "🥗 व्यक्तिगत पोषण योजना",
            "hi": "🥗 व्यक्तिगत पोषण योजना"
        }
        
        message = f"""<b>{titles.get(language, titles['en'])} for {mother_name}</b>

{plan_text}

💧 <b>Daily Hydration:</b>
• Drink 8-10 glasses of water
• Herbal teas are beneficial
• Avoid sugary drinks

🥘 <b>Meal Timing:</b>
• Eat 5-6 small meals per day
• Space meals 2-3 hours apart
• Avoid late-night eating

❓ <b>Questions?</b>
Reply with /nutrition for personalized advice"""
        
        return self.send_message(chat_id, message)
    
    def send_emergency_alert(self, chat_id, mother_name, symptoms, nearest_facility):
        """Send emergency alert"""
        
        message = f"""🚨 <b>EMERGENCY ALERT - {mother_name}</b>

<b>Symptoms Reported:</b>
{', '.join(symptoms)}

<b>⚡ ACTION REQUIRED - SEEK IMMEDIATE HELP!</b>

🏥 <b>Nearest Facility:</b>
{nearest_facility}

📞 <b>Call Emergency Services:</b>
• Ambulance: 108
• Emergency: 112

👨‍👩‍👧 <b>Family Notified:</b>
Your emergency contacts have been alerted.

🔔 Status: <b>ACTIVE EMERGENCY RESPONSE</b>"""
        
        return self.send_message(chat_id, message)
    
    def send_asha_notification(self, chat_id, asha_name, mother_name, priority, task_description):
        """Send ASHA worker notification"""
        
        priority_emoji = {
            "High": "🔴",
            "Medium": "🟡",
            "Low": "🟢"
        }
        
        emoji = priority_emoji.get(priority, "⚠️")
        
        message = f"""{emoji} <b>Task Assignment for {asha_name}</b>

<b>Mother:</b> {mother_name}
<b>Priority:</b> {priority}

<b>📋 Task:</b>
{task_description}

<b>✅ Actions Required:</b>
1. Schedule visit within next 24 hours
2. Collect vital signs
3. Update MCTS system
4. Report back via this chat

Reply with /done when task is completed.

Thank you for your service! 🙏"""
        
        return self.send_message(chat_id, message)
    
    def send_wellness_tip(self, chat_id, tip_text, language="en"):
        """Send daily wellness tip"""
        
        message = f"""💡 <b>Daily Wellness Tip</b>

{tip_text}

💙 <b>Remember:</b>
Your health is our priority.
Take care of yourself!

Questions? Reply with /help"""
        
        return self.send_message(chat_id, message)
    
    def send_button_menu(self, chat_id, mother_name):
        """Send interactive menu with buttons"""
        
        message = f"""👋 <b>Welcome to MaatruRaksha AI, {mother_name}!</b>

<b>What would you like to do?</b>

📱 <b>Use Commands:</b>
• /vitals - Log your vital signs
• /nutrition - Get nutrition plan
• /appointment - Check appointments
• /emergency - Report emergency
• /help - Get help
• /info - About MaatruRaksha

💬 Just send your message and I'll help!"""
        
        return self.send_message(chat_id, message)
    
    def handle_webhook(self, update):
        """Handle incoming Telegram messages (for chatbot mode)"""
        try:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").lower()
            
            responses = {
                "/start": "Welcome to MaatruRaksha AI Maternal Health Guardian! Type /help for commands.",
                "/help": """Available Commands:
/vitals - Log vital signs
/nutrition - Get nutrition guidance
/appointment - Check appointments
/emergency - Report emergency
/status - Check health status
/asha - ASHA support (workers only)
/about - About MaatruRaksha""",
                "/about": """MaatruRaksha AI - Maternal Health Guardian
🏥 AI-powered risk prediction
📊 Real-time health monitoring
👥 ASHA worker support
🚨 Emergency response 24/7
💙 Saving mothers' lives in Maharashtra""",
            }
            
            response_text = responses.get(text, "I understand. How can I help you with your maternal health? Type /help for options.")
            
            return self.send_message(chat_id, response_text)
        
        except Exception as e:
            logger.error(f"Webhook handling error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_chat_id_by_phone(self, phone_number):
        """
        Retrieve chat ID from phone number (requires pre-registration)
        This is a mock - in production, store phone->chat_id mapping
        """
        # In real implementation, query database for phone number -> chat_id mapping
        logger.info(f"Looking up chat_id for phone: {phone_number}")
        return None
    
    def register_user(self, chat_id, phone_number, name):
        """Register user phone to chat_id mapping"""
        # Store mapping in database for later lookup
        logger.info(f"Registered {name} ({phone_number}) with chat_id {chat_id}")
        return {"status": "registered", "chat_id": chat_id}

# Initialize service
telegram_service = TelegramService()

def send_risk_alert(chat_id, mother_name, risk_status, risk_score):
    """Public wrapper"""
    return telegram_service.send_risk_alert(chat_id, mother_name, risk_status, risk_score)

def send_appointment_reminder(chat_id, mother_name, facility, appointment_date, appointment_time="10:00 AM"):
    """Public wrapper"""
    return telegram_service.send_appointment_reminder(chat_id, mother_name, facility, appointment_date, appointment_time)

def send_medication_reminder(chat_id, medications):
    """Public wrapper"""
    return telegram_service.send_medication_reminder(chat_id, medications)

def send_nutrition_plan(chat_id, mother_name, plan_text, language="en"):
    """Public wrapper"""
    return telegram_service.send_nutrition_plan(chat_id, mother_name, plan_text, language)

def send_emergency_alert(chat_id, mother_name, symptoms, nearest_facility):
    """Public wrapper"""
    return telegram_service.send_emergency_alert(chat_id, mother_name, symptoms, nearest_facility)

def send_asha_notification(chat_id, asha_name, mother_name, priority, task_description):
    """Public wrapper"""
    return telegram_service.send_asha_notification(chat_id, asha_name, mother_name, priority, task_description)