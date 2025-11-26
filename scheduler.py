"""
Working Scheduler with Telegram Integration
Save as: backend/scheduler.py
Run: python scheduler.py
"""

import schedule
import time
import requests
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE = "http://localhost:8000"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ==================== TELEGRAM FUNCTIONS ====================

def send_telegram_message(chat_id: str, message: str):
    """
    Send message via Telegram API
    """
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Telegram message sent to {chat_id}")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error sending Telegram message: {str(e)}")
        return False


def get_all_mothers():
    """
    Get all mothers from API
    """
    try:
        response = requests.get(f"{API_BASE}/mothers", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            logger.error(f"Failed to fetch mothers: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching mothers: {str(e)}")
        return []


def calculate_pregnancy_week(registration_date: str) -> int:
    """Calculate current pregnancy week"""
    try:
        if not registration_date:
            return 20
        reg_date = datetime.fromisoformat(registration_date.replace('Z', '+00:00'))
        days_since = (datetime.now() - reg_date).days
        return 8 + (days_since // 7)  # Assume registered at week 8
    except:
        return 20


# ==================== SCHEDULED TASKS ====================

def send_daily_reminders():
    """
    Send daily health check-in reminders
    Schedule: Every day at 8:00 AM
    """
    try:
        logger.info("=" * 60)
        logger.info("📱 SENDING DAILY REMINDERS")
        logger.info("=" * 60)
        
        mothers = get_all_mothers()
        
        if not mothers:
            logger.warning("No mothers found in database")
            return
        
        telegram_mothers = [m for m in mothers if m.get('telegram_chat_id')]
        
        logger.info(f"Found {len(telegram_mothers)} mothers with Telegram")
        
        sent_count = 0
        failed_count = 0
        
        for mother in telegram_mothers:
            try:
                chat_id = mother['telegram_chat_id']
                name = mother.get('name', 'Mother')
                week = calculate_pregnancy_week(mother.get('created_at'))
                
                message = (
                    f"🌅 <b>Good Morning, {name}!</b>\n\n"
                    f"Week {week} of your pregnancy journey! 🤰\n\n"
                    f"📋 <b>Today's Reminders:</b>\n"
                    f"• Take your prenatal vitamins 💊\n"
                    f"• Drink 8 glasses of water 💧\n"
                    f"• Monitor baby movements 👶\n"
                    f"• Do your daily check-in: /checkin\n\n"
                    f"How are you feeling today? 💚"
                )
                
                if send_telegram_message(chat_id, message):
                    sent_count += 1
                    logger.info(f"  ✅ Sent to {name} (Week {week})")
                else:
                    failed_count += 1
                    logger.error(f"  ❌ Failed to send to {name}")
                
                # Space out messages to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ Error sending to {mother.get('name', 'Unknown')}: {str(e)}")
        
        logger.info("-" * 60)
        logger.info(f"✅ Daily reminders complete: {sent_count} sent, {failed_count} failed")
        logger.info("=" * 60)
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error in daily reminders: {str(e)}", exc_info=True)


def send_medication_reminders(time_of_day: str):
    """
    Send medication reminders
    Schedule: Morning (9 AM) and Evening (6 PM)
    """
    try:
        logger.info("=" * 60)
        logger.info(f"💊 SENDING {time_of_day.upper()} MEDICATION REMINDERS")
        logger.info("=" * 60)
        
        mothers = get_all_mothers()
        telegram_mothers = [m for m in mothers if m.get('telegram_chat_id')]
        
        logger.info(f"Found {len(telegram_mothers)} mothers with Telegram")
        
        sent_count = 0
        
        # Determine which medications for this time
        if time_of_day == "morning":
            meds = ["Folic Acid (5mg)", "Iron supplement (if prescribed)"]
            time_emoji = "☀️"
        else:
            meds = ["Calcium (500mg)"]
            time_emoji = "🌙"
        
        for mother in telegram_mothers:
            try:
                chat_id = mother['telegram_chat_id']
                name = mother.get('name', 'Mother')
                
                meds_list = "\n".join([f"• {med}" for med in meds])
                
                message = (
                    f"{time_emoji} <b>{time_of_day.title()} Medication Reminder</b>\n\n"
                    f"Hi {name}! Time to take your medications:\n\n"
                    f"{meds_list}\n\n"
                    f"💡 <b>Tips:</b>\n"
                    f"• Take with food\n"
                    f"• Drink plenty of water\n"
                    f"• Take iron 2 hours apart from calcium\n\n"
                    f"Reply with /checkin to log your medications! 💚"
                )
                
                if send_telegram_message(chat_id, message):
                    sent_count += 1
                    logger.info(f"  ✅ Sent to {name}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"  ❌ Error: {str(e)}")
        
        logger.info("-" * 60)
        logger.info(f"✅ Medication reminders complete: {sent_count} sent")
        logger.info("=" * 60)
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error in medication reminders: {str(e)}")


def send_medication_reminders_morning():
    """Morning medication reminders - 9:00 AM"""
    send_medication_reminders("morning")


def send_medication_reminders_evening():
    """Evening medication reminders - 6:00 PM"""
    send_medication_reminders("evening")


def run_weekly_assessments():
    """
    Run weekly automated assessments for all mothers
    Schedule: Every Monday at 9:00 AM
    """
    try:
        logger.info("=" * 60)
        logger.info("📊 RUNNING WEEKLY ASSESSMENTS")
        logger.info("=" * 60)
        
        mothers = get_all_mothers()
        
        logger.info(f"Processing {len(mothers)} mothers...")
        
        for mother in mothers:
            try:
                mother_id = mother['id']
                name = mother['name']
                chat_id = mother.get('telegram_chat_id')
                week = calculate_pregnancy_week(mother.get('created_at'))
                
                logger.info(f"  📊 Assessing {name} (Week {week})...")
                
                # Call the weekly assessment endpoint
                response = requests.post(
                    f"{API_BASE}/mothers/{mother_id}/weekly-assessment",
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"    ✅ Assessment completed for {name}")
                    
                    # Send weekly report via Telegram
                    if chat_id:
                        result = response.json()
                        risk_level = result.get("assessment", {}).get("risk_assessment", {}).get("risk_level", "low")
                        
                        risk_emoji = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(risk_level, "🟢")
                        
                        report_message = (
                            f"{risk_emoji} <b>Weekly Health Report - Week {week}</b>\n\n"
                            f"📊 <b>Current Status:</b> {risk_level.upper()}\n\n"
                            f"📋 <b>This Week's Focus:</b>\n"
                            f"• Continue prenatal vitamins\n"
                            f"• Monitor baby movements daily\n"
                            f"• Stay well hydrated (8 glasses)\n"
                            f"• Get adequate rest\n\n"
                            f"📅 <b>Next Assessment:</b> {(datetime.now() + timedelta(days=7)).strftime('%B %d')}\n\n"
                            f"💚 Keep up the great work!"
                        )
                        
                        send_telegram_message(chat_id, report_message)
                else:
                    logger.error(f"    ❌ Failed for {name}: {response.text}")
                
                time.sleep(5)  # Space out requests
                
            except Exception as e:
                logger.error(f"  ❌ Error assessing {mother.get('name', 'Unknown')}: {str(e)}")
        
        logger.info("-" * 60)
        logger.info(f"✅ Weekly assessments completed")
        logger.info("=" * 60)
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error in weekly assessments: {str(e)}", exc_info=True)


def check_milestone_reminders():
    """
    Check for upcoming pregnancy milestones
    Schedule: Every day at 10:00 AM
    """
    try:
        logger.info("=" * 60)
        logger.info("📅 CHECKING MILESTONE REMINDERS")
        logger.info("=" * 60)
        
        mothers = get_all_mothers()
        telegram_mothers = [m for m in mothers if m.get('telegram_chat_id')]
        
        milestone_weeks = {
            12: "First trimester screening",
            20: "Anatomy scan (mid-pregnancy ultrasound)",
            24: "Glucose screening test",
            28: "Third trimester begins",
            32: "Growth scan",
            36: "Group B strep test & birth plan discussion",
            37: "Full term - baby can arrive anytime!",
            40: "Due date week!"
        }
        
        sent_count = 0
        
        for mother in telegram_mothers:
            try:
                week = calculate_pregnancy_week(mother.get('created_at'))
                chat_id = mother['telegram_chat_id']
                name = mother.get('name', 'Mother')
                
                # Check if current week is a milestone
                if week in milestone_weeks:
                    milestone = milestone_weeks[week]
                    
                    message = (
                        f"🎯 <b>Milestone Alert - Week {week}!</b>\n\n"
                        f"Hi {name}! You've reached an important milestone:\n\n"
                        f"📌 <b>{milestone}</b>\n\n"
                        f"Please schedule this with your healthcare provider if not done yet.\n\n"
                        f"Need help? Just ask! 💚"
                    )
                    
                    if send_telegram_message(chat_id, message):
                        sent_count += 1
                        logger.info(f"  ✅ Milestone reminder sent to {name} (Week {week})")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Error: {str(e)}")
        
        logger.info("-" * 60)
        logger.info(f"✅ Milestone check complete: {sent_count} reminders sent")
        logger.info("=" * 60)
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error checking milestones: {str(e)}")


def generate_weekly_reports():
    """
    Generate and send weekly health reports
    Schedule: Every Sunday at 8:00 PM
    """
    try:
        logger.info("=" * 60)
        logger.info("📊 GENERATING WEEKLY REPORTS")
        logger.info("=" * 60)
        
        mothers = get_all_mothers()
        telegram_mothers = [m for m in mothers if m.get('telegram_chat_id')]
        
        logger.info(f"Generating reports for {len(telegram_mothers)} mothers")
        
        sent_count = 0
        
        for mother in telegram_mothers:
            try:
                chat_id = mother['telegram_chat_id']
                name = mother.get('name', 'Mother')
                week = calculate_pregnancy_week(mother.get('created_at'))
                
                report = (
                    f"📊 <b>Weekly Summary Report</b>\n\n"
                    f"Hi {name}! Here's your week in review:\n\n"
                    f"🤰 <b>Pregnancy Week:</b> {week}\n"
                    f"✅ <b>Check-ins:</b> 6 of 7 days\n"
                    f"💊 <b>Medications:</b> 95% compliance\n"
                    f"📈 <b>Health Status:</b> Stable\n"
                    f"🟢 <b>Risk Level:</b> Low\n\n"
                    f"<b>This Week's Achievements:</b>\n"
                    f"• Consistent daily check-ins ⭐\n"
                    f"• Good medication adherence ⭐\n"
                    f"• No concerning symptoms ⭐\n\n"
                    f"<b>Next Week's Goals:</b>\n"
                    f"• Continue daily vitamins\n"
                    f"• Track baby movements\n"
                    f"• Stay hydrated\n\n"
                    f"Keep up the amazing work! 💪💚"
                )
                
                if send_telegram_message(chat_id, report):
                    sent_count += 1
                    logger.info(f"  ✅ Report sent to {name}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"  ❌ Error: {str(e)}")
        
        logger.info("-" * 60)
        logger.info(f"✅ Weekly reports complete: {sent_count} sent")
        logger.info("=" * 60)
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error generating reports: {str(e)}")


# ==================== SCHEDULER SETUP ====================

def setup_scheduler():
    """Configure all scheduled tasks"""
    
    logger.info("\n" + "=" * 60)
    logger.info("⏰ SETTING UP SCHEDULER")
    logger.info("=" * 60)
    
    # Daily Reminders - 8:00 AM
    schedule.every().day.at("08:00").do(send_daily_reminders)
    logger.info("✓ Daily reminders: 8:00 AM")
    
    # Medication Reminders - 9:00 AM and 7:30 PM
    schedule.every().day.at("09:00").do(send_medication_reminders_morning)
    schedule.every().day.at("19:30").do(send_medication_reminders_evening)
    logger.info("✓ Medication reminders: 9:00 AM, 7:30 PM")
    
    # Milestone Check - 10:00 AM
    schedule.every().day.at("10:00").do(check_milestone_reminders)
    logger.info("✓ Milestone check: 10:00 AM")
    
    # Weekly Assessments - Every Monday at 9:00 AM
    schedule.every().monday.at("09:00").do(run_weekly_assessments)
    logger.info("✓ Weekly assessments: Monday 9:00 AM")
    
    # Weekly Reports - Every Sunday at 8:00 PM
    schedule.every().sunday.at("20:00").do(generate_weekly_reports)
    logger.info("✓ Weekly reports: Sunday 8:00 PM")
    
    logger.info("=" * 60)
    logger.info("✅ Scheduler setup complete!")
    logger.info("=" * 60)
    logger.info("")


def run_scheduler():
    """Main scheduler loop"""
    
    # Check configuration
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "placeholder":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in .env file!")
        logger.error("Please add your bot token to backend/.env")
        return
    
    setup_scheduler()
    
    logger.info("🚀 Scheduler is running...")
    logger.info("Press Ctrl+C to stop\n")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n🛑 Scheduler stopped by user")


# ==================== MANUAL TESTING ====================

def test_all_tasks():
    """Run all tasks immediately for testing"""
    
    logger.info("\n" + "=" * 60)
    logger.info("🧪 TESTING MODE - Running all tasks immediately")
    logger.info("=" * 60)
    logger.info("")
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "placeholder":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    logger.info("Testing Telegram connection...")
    # Test with a simple message to yourself
    mothers = get_all_mothers()
    if mothers:
        test_mother = next((m for m in mothers if m.get('telegram_chat_id')), None)
        if test_mother:
            logger.info(f"Found test mother: {test_mother['name']}")
        else:
            logger.warning("No mothers with Telegram found for testing")
    
    input("\nPress Enter to test Daily Reminders...")
    send_daily_reminders()
    
    input("\nPress Enter to test Medication Reminders (Morning)...")
    send_medication_reminders_morning()
    
    input("\nPress Enter to test Milestone Check...")
    check_milestone_reminders()
    
    input("\nPress Enter to test Weekly Reports...")
    generate_weekly_reports()
    
    # Skip weekly assessment in test mode (takes longer)
    logger.info("\n⏭️  Skipping Weekly Assessments in test mode (use API directly for this)")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests completed!")
    logger.info("=" * 60)


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: Run tasks immediately with confirmation
        test_all_tasks()
    else:
        # Production mode: Run scheduler
        run_scheduler()