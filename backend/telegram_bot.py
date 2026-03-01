"""
Aanchal AI - Telegram Bot

Provides conversational maternal health support, home dashboard, profile switching,
document uploads, and AI-powered answers.
"""

import os
import asyncio
import json
import html
import logging
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import tempfile
from pathlib import Path
from io import BytesIO

from gtts import gTTS
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

try:
    from backend.services.supabase_service import (
        get_mothers_by_telegram_id,
        get_recent_reports_for_mother,
        supabase,
        DatabaseService,
    )
    from backend.agents.orchestrator import route_message
    from backend.services.memory_service import save_chat_history
    from backend.services.email_service import send_alert_email
except ImportError:
    from services.supabase_service import (
        get_mothers_by_telegram_id,
        get_recent_reports_for_mother,
        supabase,
        DatabaseService,
    )
    from agents.orchestrator import route_message
    from services.memory_service import save_chat_history
    from services.email_service import send_alert_email

# Try to import conversation memory service
try:
    from services.conversation_memory import get_follow_up_context, save_conversation, extract_message_info
    CONVERSATION_MEMORY_AVAILABLE = True
except ImportError:
    CONVERSATION_MEMORY_AVAILABLE = False
    async def get_follow_up_context(mother_id, message, mother_name=""): 
        return None
    async def save_conversation(*args, **kwargs): 
        return False
    async def extract_message_info(message): 
        return {}

logger = logging.getLogger(__name__)

# States for registration (aligned with main.py)
(AWAITING_NAME, AWAITING_AGE, AWAITING_PHONE, AWAITING_DUE_DATE,
 AWAITING_LOCATION, AWAITING_GRAVIDA, AWAITING_PARITY, AWAITING_BMI,
 AWAITING_LANGUAGE, CONFIRM_REGISTRATION) = range(10)

TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
# Use BACKEND_URL for production, fall back to BACKEND_API_BASE_URL, then localhost for dev
BACKEND_API_BASE_URL = (
    os.getenv("BACKEND_URL") or 
    os.getenv("BACKEND_API_BASE_URL") or 
    "http://localhost:8000"
).strip().rstrip('/')

# Dashboard & summary configuration
MAX_TIMELINE_EVENTS = 5
MAX_MEMORIES = 5
MAX_REPORTS = 5

import re as _re

def clean_for_telegram(text: str) -> str:
    """Strip ALL markdown symbols before sending to Telegram so it renders as clean plain text."""
    if not text:
        return text
    text = _re.sub(r'\*{1,3}', '', text)                          # remove *, **, ***
    text = _re.sub(r'_{1,3}([^_\n]+)_{1,3}', r'\1', text)        # remove _italic_ / __bold__
    text = _re.sub(r'^#{1,6}\s*', '', text, flags=_re.MULTILINE)  # remove ## headers
    text = _re.sub(r'`{1,3}', '', text)                           # remove backticks
    text = _re.sub(r'^-{3,}\s*$', '', text, flags=_re.MULTILINE)  # remove --- dividers
    text = _re.sub(r'^\|.*\|\s*$', '', text, flags=_re.MULTILINE) # remove | table | rows
    text = _re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'\1: \2', text)  # [label](url) -> label: url
    text = _re.sub(r'\n{3,}', '\n\n', text)                       # collapse excess blank lines
    return text.strip()

# Language mapping for user input and callback codes
LANG_MAP = {
    # Text inputs
    "english": "en",
    "hindi": "hi",
    "marathi": "mr",
    # Callback codes
    "en": "en",
    "hi": "hi",
    "mr": "mr",
}

def _format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str[:10]


def _calculate_pregnancy_status(due_date: Optional[str]) -> Optional[str]:
    if not due_date:
        return None
    try:
        due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        conception = due - timedelta(weeks=40)
        # Use timezone-aware now if due_date is timezone-aware
        if due.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        weeks = max(0, min(42, (now - conception).days // 7))
        months = max(1, min(10, weeks // 4 or 1))
        return f"Week {weeks} (Month {months})"
    except Exception:
        return None


def _build_dashboard_keyboard(
    mothers: List[Dict[str, Any]],
    active_id: Optional[str],
    show_switch_panel: bool = False,
) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton("🚨 Alert", callback_data="action_alert")],
        [InlineKeyboardButton("📄 Health Reports", callback_data="action_summary")],
        [InlineKeyboardButton("🔁 Switch Profiles", callback_data="action_open_switch")],
        [InlineKeyboardButton("📎 Upload Documents", callback_data="action_upload_hint")],
        [InlineKeyboardButton("🆕 Register Another Mother", callback_data="action_register")],
    ]

    switch_buttons: List[List[InlineKeyboardButton]] = []
    for mother in mothers:
        mother_id = str(mother.get("id"))
        if not mother_id or mother_id == str(active_id):
            continue
        label = mother.get("name") or "Mother"
        switch_buttons.append([
            InlineKeyboardButton(f"👩 {label}", callback_data=f"switch_mother_{mother_id}")
        ])

    if show_switch_panel:
        rows.append([InlineKeyboardButton("❌ Hide Profiles", callback_data="action_close_switch")])
        rows.extend(switch_buttons)

    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    context.user_data["chat_id"] = chat_id

    mothers = await get_mothers_by_telegram_id(chat_id)
    if not mothers:
        # Display the Telegram Chat ID prominently so the user can easily share it
        await update.message.reply_text(
            "👋 *Welcome to Aanchal AI!*\n\n"
            f"📱 *Your Telegram Chat ID:* `{chat_id}`\n\n"
            "_Copy this ID and share it with your ASHA worker or Doctor if they are registering you in the system._\n\n"
            "It looks like you haven't registered yet. Use /register to add your profile "
            "or tap the *Register Mother* button below.",
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["mothers_list"] = []
        context.user_data.pop("active_mother", None)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🆕 Register Mother", callback_data="register_new")],
            [InlineKeyboardButton("📋 Copy My Chat ID", callback_data=f"copy_chat_id_{chat_id}")]
        ])
        await update.message.reply_text("Ready to onboard a mother?", reply_markup=keyboard)
        return

    context.user_data["mothers_list"] = mothers
    active = context.user_data.get("active_mother") or mothers[0]
    context.user_data["active_mother"] = active
    context.user_data["show_switch_panel"] = False

    await send_home_dashboard(update, context, mother=active, mothers=mothers, as_new_message=True)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Suspend agents and mark registration active when starting via /register
    context.chat_data['registration_active'] = True
    context.chat_data['agents_suspended'] = True
    context.user_data['registration_data'] = {}
    await update.message.reply_text("Please enter your full name:")
    return AWAITING_NAME


async def send_home_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mother: Optional[Dict[str, Any]] = None,
    mothers: Optional[List[Dict[str, Any]]] = None,
    as_new_message: bool = False,
) -> None:
    """Send or refresh the home dashboard with profile highlights and actions."""
    chat_id = context.user_data.get("chat_id") or (
        str(update.effective_chat.id) if update.effective_chat else None
    )

    if mothers is None:
        if chat_id:
            mothers = await get_mothers_by_telegram_id(chat_id)
            context.user_data["mothers_list"] = mothers
        else:
            mothers = []

    if mother is None:
        mother = context.user_data.get("active_mother") or (mothers[0] if mothers else None)

    if not mother:
        await update.effective_chat.send_message(
            "It looks like no mother profile is linked to this chat yet. Use /register to create one.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    context.user_data["active_mother"] = mother
    active_id = str(mother.get("id"))
    show_switch = context.user_data.get("show_switch_panel", False)
    keyboard = _build_dashboard_keyboard(mothers or [mother], active_id, show_switch_panel=show_switch)

    # Determine system status
    is_postnatal = mother.get("active_system") == "santanraksha" or mother.get("delivery_status") in ["delivered", "postnatal"]
    
    name = mother.get("name") or "Mother"
    location = mother.get("location") or "Not set"
    
    # Extract ASHA worker details if present on the mother record
    asha_name = mother.get("asha_name") or mother.get("asha_worker_name")
    asha_phone = mother.get("asha_phone") or mother.get("asha_worker_phone")
    if not asha_name and isinstance(mother.get("asha_worker"), dict):
        asha_name = mother["asha_worker"].get("name")
        asha_phone = asha_phone or mother["asha_worker"].get("phone")

    # Build Dashboard Lines
    lines = [f"👋 *Welcome back, {name}!*", ""]
    
    if chat_id:
        lines.append(f"🆔 *Telegram Chat ID:* `{chat_id}`")
    
    lines.append(f"👩‍🍼 *Active Profile:* {name}")
    lines.append(f"📍 *Location:* {location}")

    if is_postnatal:
        # Postnatal Dashboard Fields
        delivery_date = _format_date(mother.get("delivery_date"))
        lines.append(f"🎉 *Status:* Delivered (SantanRaksha)")
        
        if mother.get("delivery_date"):
            # Calculate baby age / days postpartum
            try:
                del_dt = datetime.fromisoformat(mother.get("delivery_date").replace("Z", "+00:00"))
                days_diff = (datetime.now(del_dt.tzinfo) - del_dt).days
                if days_diff < 30:
                    age_text = f"{days_diff} days old"
                else:
                    age_text = f"{days_diff // 30} months old"
                lines.append(f"👶 *Baby Age:* {age_text}")
            except Exception:
                lines.append(f"📅 *Delivery Date:* {delivery_date}")
        
        lines.append("💉 *Next Vaccine:* Check 'Health Reports'")
    else:
        # Pregnancy Dashboard Fields
        pregnancy_line = _calculate_pregnancy_status(mother.get("due_date"))
        due_line = _format_date(mother.get("due_date"))
        lines.append(f"📅 *Due Date:* {due_line}")
        if pregnancy_line:
            lines.append(f"🤰 *Pregnancy:* {pregnancy_line}")

    # Common ASHA line
    if asha_name:
        lines.append(f"🧑‍⚕️ *ASHA Worker:* {asha_name}" + (f" ({asha_phone})" if asha_phone else ""))

    lines.append("")
    lines.append(
        "Use the buttons below to view your health summary, upload documents, "
        "or switch between registered mothers."
    )

    text = "\n".join(filter(None, lines))

    cbq = getattr(update, "callback_query", None)
    if cbq and not as_new_message:
        logger.info("Editing existing message to show dashboard")
        await cbq.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    else:
        chat = getattr(update, "effective_chat", None)
        try:
            if chat:
                logger.info("Sending dashboard as a new message via effective_chat")
                await chat.send_message(
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
            else:
                # Fallback: update may be a Message
                logger.info("Sending dashboard as a reply to the message target")
                await update.reply_text(
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
        except Exception:
            # Final fallback via bot.send_message
            if chat_id:
                logger.info("Sending dashboard via bot.send_message fallback")
                await context.bot.send_message(
                    chat_id,
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )


async def handle_home_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard action buttons."""
    query = update.callback_query
    action = query.data.replace("action_", "", 1)

    # Block all actions except starting registration when registration is active
    if context.chat_data.get('registration_active') and action != "register":
        await query.answer()
        await query.message.reply_text("Finish registration first or send /cancel.")
        return

    if action == "summary":
        await query.answer("Fetching summary…")
        await action_summary(update, context)
    elif action == "alert":
        await query.answer()
        mother = context.user_data.get("active_mother")
        name = (mother or {}).get("name") or "Mother"
        text = f"Send alert to assigned ASHA worker and doctor for {name}?"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="action_confirm_alert")],
            [InlineKeyboardButton("❌ Cancel", callback_data="action_cancel_alert")],
        ])
        await query.message.reply_text(text, reply_markup=keyboard)
    elif action == "confirm_alert":
        await query.answer()
        await _perform_alert_send(update, context)
    elif action == "cancel_alert":
        await query.answer("Cancelled")
    elif action == "register":
        await query.answer()
        await _prompt_registration(query)
    elif action == "upload_hint":
        await query.answer("Upload a PDF/image as a message.", show_alert=True)
    elif action == "open_switch":
        await query.answer("Choose a profile to make it active.")
        context.user_data["show_switch_panel"] = True
        await send_home_dashboard(update, context, as_new_message=False)
    elif action == "close_switch":
        await query.answer("Hiding switch panel.")
        context.user_data["show_switch_panel"] = False
        await send_home_dashboard(update, context, as_new_message=False)
    else:
        await query.answer()

async def _perform_alert_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mother = context.user_data.get("active_mother")
    if not mother:
        await update.callback_query.message.reply_text("No active mother profile")
        return
    mother_id = mother.get("id")
    profile = DatabaseService.get_mother_holistic_data(mother_id)
    asha = profile.get("asha_worker") or {}
    doctor = profile.get("doctor") or {}
    mother_data = profile.get("profile") or {}
    mother_name = mother_data.get("name") or "Mother"
    mother_phone = mother_data.get("phone") or ""
    location = mother_data.get("location") or ""
    
    sent_to = []
    
    # Send email to ASHA worker
    asha_email = asha.get("email")
    if asha_email:
        result = send_alert_email(
            to_email=asha_email,
            recipient_name=asha.get("name", "ASHA Worker"),
            recipient_role="ASHA Worker",
            mother_name=mother_name,
            mother_id=str(mother_id),
            mother_phone=mother_phone,
            location=location,
            alert_type="emergency"
        )
        if result.get("status") == "sent":
            sent_to.append(f"ASHA: {asha.get('name')}")
            logger.info(f"✅ Alert email sent to ASHA worker: {asha_email}")
    
    # Send email to Doctor
    doctor_email = doctor.get("email")
    if doctor_email:
        result = send_alert_email(
            to_email=doctor_email,
            recipient_name=doctor.get("name", "Doctor"),
            recipient_role="Doctor",
            mother_name=mother_name,
            mother_id=str(mother_id),
            mother_phone=mother_phone,
            location=location,
            alert_type="emergency"
        )
        if result.get("status") == "sent":
            sent_to.append(f"Doctor: {doctor.get('name')}")
            logger.info(f"✅ Alert email sent to Doctor: {doctor_email}")
    
    cbq = update.callback_query
    if sent_to:
        await cbq.message.reply_text(f"✅ Alert emails sent to: {', '.join(sent_to)}")
    else:
        await cbq.message.reply_text("⚠️ Alert could not be sent. No email addresses configured for assigned contacts.")


async def _prompt_registration(query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Register Mother", callback_data="register_new")]
    ])
    await query.message.reply_text(
        "Tap below to start the maternal profile registration flow.",
        reply_markup=keyboard,
    )

async def register_button_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        context.user_data['registration_data'] = {}
        # Suspend agents and mark registration active
        context.chat_data['registration_active'] = True
        context.chat_data['agents_suspended'] = True
        await query.message.reply_text("Please enter your full name:")
    else:
        # Suspend agents and mark registration active
        context.chat_data['registration_active'] = True
        context.chat_data['agents_suspended'] = True
        await update.effective_chat.send_message("Please enter your full name:")
    return AWAITING_NAME


async def action_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display an enriched health summary for the active mother."""
    query = update.callback_query
    mother = context.user_data.get("active_mother")
    if not mother:
        await query.message.reply_text("⚠️ No active mother profile. Please register first.")
        return

    mother_id = str(mother.get("id"))
    name = mother.get("name", "Mother")
    summary_lines = [
        f"<b>📊 Health Summary for {html.escape(name)}</b>",
        f"<b>🆔 Mother ID:</b> <code>{html.escape(mother_id)}</code>",
    ]

    # Only show pregnancy info if NOT delivered
    delivery_status = mother.get("delivery_status", "pregnant")
    is_postnatal = delivery_status in ["delivered", "postnatal"]
    
    if is_postnatal:
        # Show postnatal/SantanRaksha info
        summary_lines.append(f"<b>👶 Status:</b> Delivered (SantanRaksha)")
        if mother.get("delivery_date"):
            summary_lines.append(f"<b>📅 Delivery Date:</b> {html.escape(_format_date(mother.get('delivery_date')))}")
        # Calculate baby age
        try:
            from datetime import datetime
            delivery_date = mother.get("delivery_date")
            if delivery_date:
                if isinstance(delivery_date, str):
                    delivery_date = datetime.fromisoformat(delivery_date.replace('Z', '+00:00'))
                days_old = (datetime.now(delivery_date.tzinfo) - delivery_date).days if delivery_date.tzinfo else (datetime.now() - delivery_date).days
                if days_old >= 0:
                    summary_lines.append(f"<b>👶 Baby Age:</b> {days_old} days old")
        except Exception:
            pass
    else:
        # Show pregnancy info
        pregnancy_status = _calculate_pregnancy_status(mother.get("due_date"))
        if pregnancy_status:
            summary_lines.append(f"<b>🤰 Pregnancy:</b> {html.escape(pregnancy_status)}")
        if mother.get("due_date"):
            summary_lines.append(f"<b>📅 Due Date:</b> {html.escape(_format_date(mother.get('due_date')))}")
    
    if mother.get("location"):
        summary_lines.append(f"<b>📍 Location:</b> {html.escape(mother.get('location'))}")
    # Use a plain newline separator instead of unsupported <br>
    summary_lines.append("")

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_API_BASE_URL}/api/v1/summary/{mother_id}"
            timeout = aiohttp.ClientTimeout(total=25)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Summary API returned {resp.status}")
                summary_payload = await resp.json()
    except Exception as exc:
        logger.error(f"Summary endpoint failed: {exc}")
        summary_lines.append("⚠️ Unable to fetch latest summary right now. Please try again later.")
        await query.message.reply_text(
            "\n".join(summary_lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    recent_timeline = summary_payload.get("recent_timeline", [])[:MAX_TIMELINE_EVENTS]
    key_memories = summary_payload.get("key_memories", [])[:MAX_MEMORIES]
    reports = await get_recent_reports_for_mother(mother_id, limit=MAX_REPORTS)

    if recent_timeline:
        summary_lines.append("<b>🗂 Key Timeline Events:</b>")
        for event in recent_timeline:
            date = _format_date(event.get("event_date") or event.get("date") or event.get("created_at"))
            text = event.get("summary") or event.get("event_summary") or "Update"
            summary_lines.append(f"• {html.escape(date)}: {html.escape(text)}")
        summary_lines.append("")

    if key_memories:
        summary_lines.append("<b>🧠 Important Notes:</b>")
        for memory in key_memories:
            summary_lines.append(
                f"• {html.escape(str(memory.get('memory_key', 'Note')))}: "
                f"{html.escape(str(memory.get('memory_value', '')))}"
            )
        summary_lines.append("")

    if reports:
        summary_lines.append("<b>📎 Uploaded Documents:</b>")
        for report in reports:
            title = report.get("file_name") or report.get("filename") or "Document"
            uploaded_at = _format_date(report.get("uploaded_at") or report.get("created_at"))
            analysis_summary = report.get("analysis_summary")
            file_url = report.get("file_url") or report.get("file_path")
            
            # Create clickable hyperlink if file_url is available
            if file_url:
                # Escape HTML special characters in title but keep the link functional
                safe_title = html.escape(title)
                summary_lines.append(f"• {html.escape(uploaded_at)} — <a href=\"{file_url}\">{safe_title} 📄</a>")
            else:
                summary_lines.append(f"• {html.escape(uploaded_at)} — {html.escape(title)}")
            
            if analysis_summary:
                summary_lines.append(f"  ↳ {html.escape(str(analysis_summary))}")
        summary_lines.append("")
    else:
        summary_lines.append("📎 No documents uploaded yet.")
        summary_lines.append("")


    if summary_payload.get("summary") and isinstance(summary_payload["summary"], dict):
        overview = summary_payload["summary"]
        recommendations = overview.get("recommendations")
        risks = overview.get("risk_flags") or overview.get("risks")
        if recommendations:
            summary_lines.append("<b>✅ Recommendations:</b>")
            if isinstance(recommendations, list):
                for rec in recommendations[:5]:
                    summary_lines.append(f"• {html.escape(str(rec))}")
            else:
                summary_lines.append(f"• {html.escape(str(recommendations))}")
            summary_lines.append("")
        if risks:
            summary_lines.append("<b>⚠️ Risks / Alerts:</b>")
            if isinstance(risks, list):
                for risk in risks[:5]:
                    summary_lines.append(f"• {html.escape(str(risk))}")
            else:
                summary_lines.append(f"• {html.escape(str(risks))}")
            summary_lines.append("")

    summary_lines.append("💬 Ask me anything for personalized guidance based on these records.")

    await query.message.reply_text(
        "\n".join(summary_lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def handle_switch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle switching between registered mothers via inline buttons."""
    query = update.callback_query
    await query.answer()

    # Block switching during active registration
    if context.chat_data.get('registration_active'):
        await query.message.reply_text("Finish registration first or send /cancel.")
        return

    mother_id = query.data.replace("switch_mother_", "", 1)
    chat_id = context.user_data.get("chat_id") or str(query.message.chat.id)

    mothers = context.user_data.get("mothers_list")
    if not mothers:
        mothers = await get_mothers_by_telegram_id(chat_id)
        context.user_data["mothers_list"] = mothers

    target = next((m for m in mothers if str(m.get("id")) == mother_id), None)
    if not target:
        await query.message.reply_text("⚠️ Could not find that profile. Please try again.")
        return

    context.user_data["active_mother"] = target
    context.user_data["show_switch_panel"] = False
    await send_home_dashboard(update, context, as_new_message=False)


async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF/image uploads and push them to Supabase for analysis."""
    # Block uploads during active registration
    if context.chat_data.get('registration_active'):
        await update.message.reply_text("Finish registration first or send /cancel.")
        return

    chat_id = str(update.effective_chat.id)
    context.user_data["chat_id"] = chat_id

    mother = context.user_data.get("active_mother")
    mothers = context.user_data.get("mothers_list")
    if not mother:
        if not mothers:
            mothers = await get_mothers_by_telegram_id(chat_id)
            context.user_data["mothers_list"] = mothers
        if mothers:
            mother = mothers[0]
            context.user_data["active_mother"] = mother

    if not mother:
        await update.message.reply_text(
            "⚠️ No mother profile found. Use /register to add one before uploading reports."
        )
        return

    mother_id = mother.get("id")
    document = update.message.document
    photo = update.message.photo
    file_info = None
    filename = ""
    file_type = ""

    try:
        if document:
            file_info = await context.bot.get_file(document.file_id)
            filename = document.file_name or f"document_{document.file_id}"
            file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
        elif photo:
            largest_photo = max(photo, key=lambda p: p.file_size or 0)
            file_info = await context.bot.get_file(largest_photo.file_id)
            filename = f"photo_{largest_photo.file_id}.jpg"
            file_type = "jpg"
        else:
            await update.message.reply_text("Please send a PDF or image to upload.")
            return

        if file_type not in ["pdf", "jpg", "jpeg", "png", "webp"]:
            await update.message.reply_text(
                f"❌ Unsupported file type: {file_type}. Please upload PDF or image files."
            )
            return

        processing_msg = await update.message.reply_text(
            f"📄 Received *{filename}*\n"
            f"⏳ Uploading to your health records...",
            parse_mode=ParseMode.MARKDOWN,
        )

        file_url = file_info.file_path
        if not file_url.startswith("http"):
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_url}"

        report_id = str(uuid4())
        insert_data = {
            "id": report_id,
            "mother_id": mother_id,
            "telegram_chat_id": chat_id,
            "file_name": filename,
            "file_type": file_type,
            "file_url": file_url,
            "file_path": file_url,
            "uploaded_at": datetime.now().isoformat(),
            "analysis_status": "processing",
            "created_at": datetime.now().isoformat(),
        }

        supabase.table("medical_reports").insert(insert_data).execute()

        try:
            async with aiohttp.ClientSession() as session:
                analyze_url = f"{BACKEND_API_BASE_URL}/analyze-report"
                payload = {
                    "mother_id": str(mother_id),
                    "report_id": report_id,
                    "file_url": file_url,
                    "file_type": file_type,
                }
                timeout = aiohttp.ClientTimeout(total=60)
                async with session.post(analyze_url, json=payload, timeout=timeout) as resp:
                    if resp.status == 200:
                        analysis = await resp.json()
                        concerns = analysis.get("concerns") or []
                        risk_level = (analysis.get("risk_level") or "normal").upper()
                        msg = (
                            f"✅ *Document uploaded & analyzed!*\n\n"
                            f"📄 File: {filename}\n"
                            f"📊 Risk Level: {risk_level}\n"
                        )
                        if concerns:
                            msg += "⚠️ Concerns:\n"
                            for concern in concerns[:3]:
                                msg += f"• {concern}\n"
                        msg += "\nUse /start to refresh your dashboard."
                        await processing_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await processing_msg.edit_text(
                            "✅ Document uploaded!\n\n"
                            "Analysis will continue in the background. "
                            "Check back in a minute.",
                            parse_mode=ParseMode.MARKDOWN,
                        )
        except Exception as api_error:
            logger.error(f"Document analysis error: {api_error}")
            await processing_msg.edit_text(
                "✅ Document uploaded!\n\n"
                "Analysis is running in the background.",
                parse_mode=ParseMode.MARKDOWN,
            )

        await save_chat_history(
            mother_id,
            "document",
            f"Uploaded document {filename}",
            telegram_chat_id=chat_id,
        )
    except Exception as exc:
        logger.error(f"Document upload failed: {exc}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error uploading document: {exc}\nPlease try again."
        )

async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle both text replies and button callbacks
    query = update.callback_query
    if query:
        await query.answer()
        data = (query.data or "").strip()
        code = data.replace("lang_", "", 1) if data.startswith("lang_") else data
        lang = LANG_MAP.get(code.lower())
        target = query.message
    else:
        text = (update.message.text or "").strip().lower()
        lang = LANG_MAP.get(text)
        target = update.message

    if not lang:
        await target.reply_text("Please choose a valid language: English, Hindi, or Marathi.")
        return AWAITING_LANGUAGE

    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['preferred_language'] = lang

    await target.reply_text("Processing your registration...")
    return await finalize_registration(target, context)

# === Wrapper bot class to match main.py expectations ===
class MatruRakshaBot:
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await register_button_entry(update, context)

    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_name"](update, context)

    async def receive_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_age"](update, context)

    async def receive_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_phone"](update, context)

    async def receive_due_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_due_date"](update, context)

    async def receive_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_location"](update, context)

    async def receive_gravida(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_gravida"](update, context)

    async def receive_parity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_parity"](update, context)

    async def receive_bmi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_bmi"](update, context)

    async def receive_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["receive_language"](update, context)

    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["confirm_registration"](update, context)

    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["cancel_registration"](update, context)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["start"](update, context)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await globals()["handle_voice_message"](update, context)

# Backward-compatibility alias for typo
MatruRakkshaBot = MatruRakshaBot

# === Minimal registration step handlers (module-level) ===
async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['name'] = None if text.lower() == "skip" else text
    await update.message.reply_text("Please enter your age (or type 'skip').")
    return AWAITING_AGE

async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    try:
        value = int(text)
    except Exception:
        value = None
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['age'] = value
    await update.message.reply_text("Please enter your phone number (or type 'skip').")
    return AWAITING_PHONE

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice messages:
    1. STT: Transcribe using Gemini
    2. Process: Route entire text to orchestrator
    3. TTS: Convert response to Audio and reply
    """
    # Block voice during registration for simplicity (or we could support it, but risky)
    if context.chat_data.get('registration_active'):
        await update.message.reply_text("Please type your details for registration.")
        return

    # User feedback: "Listening..."
    status_msg = await update.message.reply_text("🎤 Listening and processing...")

    try:
        voice = update.message.voice or update.message.audio
        if not voice:
            await status_msg.edit_text("⚠️ No voice detected.")
            return

        # 1. Download file
        file_id = voice.file_id
        file = await context.bot.get_file(file_id)
        
        # Use temp dir for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "voice_input.oga"
            await file.download_to_drive(file_path)

            # 2. Transcribe with Gemini (STT)
            # We use the same Gemini client initialized in main.py, but need access here.
            # Best way: Check if agent system has one or just use direct REST if needed.
            # Assuming main.py has `gemini_client` but we are in telegram_bot.py.
            # We'll use the orchestrator's LLM capability or local genai import if configured.
            
            try:
                from google import genai
                TRANSCRIPTION_MODEL = "gemini-2.5-flash" # Faster for audio
                if not os.getenv("GEMINI_API_KEY"):
                    raise ValueError("No Gemini API Key")
                
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                
                # Upload/Process audio bytes directly
                # Run file read in thread to avoid blocking event loop
                def read_file_sync(path):
                    with open(path, "rb") as f:
                        return f.read()
                
                audio_bytes = await asyncio.to_thread(read_file_sync, file_path)
                
                # Prompt for transcription
                response = client.models.generate_content(
                    model=TRANSCRIPTION_MODEL,
                    contents=[
                        "Transcribe this audio exactly. Return ONLY the text, no preamble.",
                        genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
                    ]
                )
                user_text = response.text.strip()
                
                if not user_text:
                    await status_msg.edit_text("⚠️ Could not hear anything clearly. Please try again.")
                    return
                
                # Show what was heard
                await status_msg.edit_text(f"🗣️ You said: *\"{user_text}\"*", parse_mode=ParseMode.MARKDOWN)
                
                # 3. Route to Orchestrator
                # Need mother context
                mother = context.user_data.get("active_mother")
                if not mother:
                    # Try fetch default
                    chat_id = str(update.effective_chat.id)
                    mothers = await get_mothers_by_telegram_id(chat_id)
                    if mothers:
                        mother = mothers[0]
                        context.user_data["active_mother"] = mother
                
                # route_message expects (message, mother_data, reports_context, chat_history)
                # We interpret this as a general query
                
                reply_text = "I can only help if you have a registered profile. Type /register to start."
                if mother:
                    # Send thinking action
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    
                    # Call Orchestrator — route_message returns a string
                    reply_text = await route_message(
                        message=user_text,
                        mother_context=mother,
                        reports_context=[],
                    )
                    if not reply_text:
                        reply_text = "I'm not sure how to help with that."

                # 4. Text-to-Speech (TTS)
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")
                
                # Detect language from mother profile for TTS
                tts_lang = 'en'
                if mother:
                    pref_lang = mother.get('preferred_language', 'en')
                    if pref_lang in ('hi', 'mr'):  # gTTS supports hi, mr
                        tts_lang = pref_lang
                
                try:
                    tts = gTTS(reply_text, lang=tts_lang, tld='co.in')
                    audio_io = BytesIO()
                    tts.write_to_fp(audio_io)
                    audio_io.seek(0)
                    
                    # 5. Send Voice Reply
                    await update.message.reply_voice(
                        voice=audio_io,
                        caption=f"{reply_text[:200]}..." if len(reply_text) > 200 else reply_text
                    )
                except Exception as tts_err:
                    logger.warning(f"TTS failed, sending text only: {tts_err}")
                
                # Send full text as backup
                await update.message.reply_text(reply_text)

            except Exception as e:
                logger.error(f"Voice processing error: {e}", exc_info=True)
                await status_msg.edit_text("❌ Sorry, I couldn't process your voice message. Please try typing.")

    except Exception as e:
        logger.error(f"Voice handler fatal error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Error processing voice.")


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    value = None if text.lower() == "skip" else text
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['phone'] = value
    await update.message.reply_text("Please enter your due date in YYYY-MM-DD (or 'skip').")
    return AWAITING_DUE_DATE

async def receive_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    value = None if text.lower() == "skip" else text
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['due_date'] = value
    await update.message.reply_text("Please enter your city/location (or 'skip').")
    return AWAITING_LOCATION

async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    value = None if text.lower() == "skip" else text
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['location'] = value
    await update.message.reply_text("Please enter gravida (number of pregnancies, or 'skip').")
    return AWAITING_GRAVIDA

async def receive_gravida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    try:
        value = int(text)
    except Exception:
        value = None
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['gravida'] = value
    await update.message.reply_text("Please enter parity (number of births, or 'skip').")
    return AWAITING_PARITY

async def receive_parity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    try:
        value = int(text)
    except Exception:
        value = None
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['parity'] = value
    await update.message.reply_text("Please enter BMI (e.g., 22.5, or 'skip').")
    return AWAITING_BMI

async def receive_bmi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    try:
        value = float(text)
    except Exception:
        value = None
    context.user_data.setdefault('registration_data', {})
    context.user_data['registration_data']['bmi'] = value
    # Prompt for language selection (text input acceptable)
    await update.message.reply_text("Choose your preferred language: English, Hindi, or Marathi. You can type the language name.")
    return AWAITING_LANGUAGE

# === Finalize registration and persist to Supabase ===
async def finalize_registration(target, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get('registration_data', {})
    chat_id = str(getattr(getattr(target, 'chat', None), 'id', '') or (getattr(getattr(target, 'from_user', None), 'id', '') or ''))

    payload = {
        "name": data.get("name") or "Unknown",
        "age": data.get("age"),
        "phone": data.get("phone") or "0000000000",
        "due_date": data.get("due_date"),
        "location": data.get("location"),
        "gravida": data.get("gravida"),
        "parity": data.get("parity"),
        "bmi": data.get("bmi"),
        "preferred_language": data.get("preferred_language") or "en",
        "telegram_chat_id": chat_id,
    }

    try:
        logger.info(f"Attempting mother registration insert: {payload}")
        res = supabase.table("mothers").insert(payload).execute()
        logger.info(f"Supabase insert result: {getattr(res, 'data', None)}")
        mother = res.data[0] if hasattr(res, 'data') and res.data else None
        try:
            verify_resp = supabase.table("mothers").select("*").eq("telegram_chat_id", chat_id).order("created_at", desc=True).limit(1).execute()
            logger.info(f"Post-insert verification: {getattr(verify_resp, 'data', None)}")
        except Exception as v_err:
            logger.error(f"Verification query failed: {v_err}")
        assigned = None
        if mother:
            try:
                from backend.services.supabase_service import DatabaseService
            except ImportError:
                from services.supabase_service import DatabaseService
            assigned = DatabaseService.assign_asha_worker_to_mother(mother.get('id'), mother.get('location'))
            DatabaseService.assign_doctor_to_mother(mother.get('id'), mother.get('location'))
        # // Clear registration state flags and temp data
        context.chat_data['registration_active'] = False
        context.chat_data['agents_suspended'] = False
        context.user_data.pop('registration_data', None)

        if assigned and isinstance(assigned, dict):
            msg = f"✅ Registration Complete. Your Assigned ASHA Worker is: {assigned.get('name')} ({assigned.get('phone')})."
        else:
            msg = "✅ Registration saved!"
        await target.reply_text(msg)
        mothers = await get_mothers_by_telegram_id(chat_id) if callable(get_mothers_by_telegram_id) else None
        await send_home_dashboard(target, context, mother=mother, mothers=mothers, as_new_message=True)
    except Exception as exc:
        logger.error(f"Registration save failed: {exc}", exc_info=True)
        try:
            logger.error(f"Failed payload: {payload}")
        except Exception:
            pass
        await target.reply_text("⚠️ Could not save registration right now. Please try again later.")
    return ConversationHandler.END

# === Confirm registration callback ===
async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = (getattr(query, 'data', '') or '')
    action = data.split('_', 1)[1] if data.startswith('confirm_') else data
    target = query.message
    if action in ('yes','accept','ok','confirm','y'):
        await target.reply_text('Processing your registration...')
        return await finalize_registration(target, context)
    else:
        await target.reply_text('Registration not confirmed. You can update details or restart with /start.')
        return ConversationHandler.END

# === Cancel registration command ===
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear any in-progress registration data and end the conversation
    try:
        context.user_data.pop('registration_data', None)
    except Exception:
        pass
    context.chat_data['registration_active'] = False
    context.chat_data['agents_suspended'] = False
    await update.message.reply_text('Registration cancelled. You can start again anytime with /start.')
    return ConversationHandler.END

# === Minimal text handler to satisfy imports ===
# --- Global Query Cache to save tokens for identical/frequent questions ---
import time
_query_cache = {}  # { "text": (reply, timestamp) }
CACHE_TTL = 3600 * 24  # 24 hours

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text.startswith("/"):
        return
    
    # Block messages during active registration
    if context.chat_data.get('registration_active'):
        return
        
    # --- Daily User Throttling (20 messages/day) to save API tokens ---
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if context.user_data.get("throttle_date") != today_str:
        context.user_data["throttle_date"] = today_str
        context.user_data["message_count"] = 0
        
    context.user_data["message_count"] = context.user_data.get("message_count", 0) + 1
    
    if context.user_data["message_count"] > 20:
        await update.message.reply_text(
            "⚠️ You have reached your daily limit of 20 health queries. "
            "Our AI assistants require processing time. Please come back tomorrow, "
            "or if it's an emergency, call 108 immediately."
        )
        return
    # -----------------------------------------------------------------
    
    try:
        chat_id = str(getattr(getattr(update, 'message', None), 'chat', None).id)
    except Exception:
        chat_id = None
    
    # Store chat_id for later use
    context.user_data["chat_id"] = chat_id
    
    # IMPORTANT: Use the active_mother from context if available, otherwise fetch and use first
    mother = context.user_data.get("active_mother")
    mothers = context.user_data.get("mothers_list")
    
    # If no active mother in context, fetch from database
    if not mother:
        try:
            mothers = await get_mothers_by_telegram_id(chat_id) if callable(get_mothers_by_telegram_id) else []
            context.user_data["mothers_list"] = mothers
            if mothers:
                mother = mothers[0]
                context.user_data["active_mother"] = mother
        except Exception:
            mothers = []
            mother = None
    
    # Log which mother context is being used for debugging
    if mother:
        logger.info(f"📱 Processing message for mother: {mother.get('name')} (ID: {mother.get('id')})")
    
    mother_context = mother or {"preferred_language": "en"}
    mother_id = mother_context.get('id') if isinstance(mother_context, dict) else None
    
    # Check for active doctor/ASHA conversation
    # Logic: 
    # 1. EMERGENCY keywords ALWAYS get AI response + alert (bypass doctor mode)
    # 2. If mother addresses doctor/ASHA directly (keywords), start new conversation
    # 3. If there's recent activity in case_discussions, keep AI silent
    # 4. Only resume AI if no case_discussion activity for 30 minutes
    skip_ai_response = False
    sender_role = "doctor"  # Default for message
    
    # EMERGENCY keywords - these ALWAYS get AI response, NEVER silently routed
    emergency_keywords = [
        # English
        'blood loss', 'bleeding', 'blood', 'hemorrhage', 'haemorrhage',
        'severe pain', 'unbearable pain', 'cant breathe', "can't breathe", 'difficulty breathing',
        'unconscious', 'fainted', 'fainting', 'collapsed', 'seizure', 'convulsion',
        'baby not moving', 'no movement', 'water broke', 'water break', 'labor',
        'emergency', 'urgent', 'help me', 'dying', 'hospital', 'ambulance',
        'headache', 'blurred vision', 'swelling', 'high fever', 'chest pain',
        # Hindi (Devanagari)
        'खून', 'रक्तस्राव', 'दर्द', 'तेज दर्द', 'बेहोश', 'सांस',
        'मदद', 'इमरजेंसी', 'अस्पताल', 'एम्बुलेंस', 'बुखार', 'दौरा',
        # Hindi (transliterated — critical for Roman-script users)
        'khoon', 'dard', 'tez dard', 'behosh', 'saans', 'madad',
        'bukhar', 'daura', 'bacha nahi hil raha',
        # Marathi (Devanagari)
        'रक्त', 'वेदना', 'बेशुद्ध', 'श्वास', 'मदत', 'इमर्जन्सी', 'हॉस्पिटल', 'ताप',
    ]
    text_lower = text.lower()
    is_emergency = any(keyword in text_lower for keyword in emergency_keywords)
    
    # Greeting detection - give SHORT responses for simple greetings
    greeting_keywords = [
        # English
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'good night', 'thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay',
        # Hindi/Marathi
        'नमस्कार', 'नमस्ते', 'namaste', 'namaskar', 'धन्यवाद', 'शुभ', 'जय',
        'हाय', 'हेलो', 'ठीक', 'अच्छा', 'बाय',
    ]
    # Check if message is ONLY a greeting (short message, no other content)
    is_greeting = (
        len(text.split()) <= 3 and  # Very short message
        any(keyword in text_lower for keyword in greeting_keywords)
    )
    
    if is_greeting and not is_emergency:
        # Give a short, friendly response based on language
        name = mother.get('name', '') if mother else ''
        greeting_responses = {
            'mr': f"🙏 नमस्कार{', ' + name if name else ''}! मी तुमच्या मदतीसाठी येथे आहे. काही प्रश्न असल्यास विचारा.",
            'hi': f"🙏 नमस्ते{', ' + name if name else ''}! मैं आपकी मदद के लिए यहाँ हूँ। कोई भी सवाल पूछें।",
            'en': f"🙏 Hello{', ' + name if name else ''}! I'm here to help. Feel free to ask any questions."
        }
        lang = mother.get('preferred_language', 'en') if mother else 'en'
        reply = greeting_responses.get(lang, greeting_responses['en'])
        await update.message.reply_text(reply)
        return
    
    # Keywords that indicate mother wants to talk to doctor/ASHA (not AI)
    doctor_keywords = [
        'doctor', 'dr.', 'dr ', 'asha', 'nurse', 'didi',  # Common terms
        'डॉक्टर', 'आशा', 'दीदी',  # Hindi
        'डॉक्टर', 'आशा', 'ताई',  # Marathi
    ]
    addressing_doctor = any(keyword in text_lower for keyword in doctor_keywords)
    
    # EMERGENCY messages ALWAYS bypass doctor mode
    if is_emergency:
        logger.info(f"🚨 EMERGENCY detected in message: '{text[:50]}...' - forcing AI response")
        addressing_doctor = False  # Don't route to doctor, let AI handle it
    
    if mother_id:
        try:
            from datetime import datetime, timedelta
            
            # Get the LAST message in case_discussions (from anyone)
            result = supabase.table("case_discussions")\
                .select("created_at, sender_role, sender_name")\
                .eq("mother_id", str(mother_id))\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                last_msg = result.data[0]
                last_msg_time = datetime.fromisoformat(last_msg['created_at'].replace('Z', '+00:00'))
                now = datetime.now(last_msg_time.tzinfo) if last_msg_time.tzinfo else datetime.now()
                time_diff = now - last_msg_time.replace(tzinfo=None) if not last_msg_time.tzinfo else now - last_msg_time
                
                # Also check if a doctor/ASHA has EVER messaged (to confirm it's an active convo)
                doctor_check = supabase.table("case_discussions")\
                    .select("id")\
                    .eq("mother_id", str(mother_id))\
                    .in_("sender_role", ["DOCTOR", "ASHA"])\
                    .limit(1)\
                    .execute()
                
                has_doctor_messages = bool(doctor_check.data)
                
                # Skip AI if:
                # 1. NOT an emergency, AND
                # 2. Mother is addressing doctor directly (keywords detected), OR
                # 3. There's active conversation (activity in last 30 min AND doctor has messaged)
                # EMERGENCY messages ALWAYS get AI response regardless of doctor conversation
                if not is_emergency and (addressing_doctor or (has_doctor_messages and time_diff < timedelta(minutes=30))):
                    skip_ai_response = True
                    sender_role = last_msg.get('sender_role', 'Doctor')
                    if sender_role == "MOTHER":
                        # Find the doctor who started the conversation
                        doc_result = supabase.table("case_discussions")\
                            .select("sender_role, sender_name")\
                            .eq("mother_id", str(mother_id))\
                            .in_("sender_role", ["DOCTOR", "ASHA"])\
                            .order("created_at", desc=True)\
                            .limit(1)\
                            .execute()
                        if doc_result.data:
                            sender_role = doc_result.data[0].get('sender_role', 'Doctor')
                    
                    logger.info(f"🔇 Skipping AI - active case discussion (last activity {time_diff.seconds//60}m ago)")
                    
                    # Store mother's reply in case_discussions
                    try:
                        supabase.table("case_discussions").insert({
                            "mother_id": str(mother_id),
                            "sender_role": "mother",
                            "sender_name": mother.get('name', 'Mother'),
                            "message": text,
                        }).execute()
                        logger.info(f"💬 Mother's reply saved to case_discussions")
                    except Exception as db_err:
                        logger.error(f"Failed to save mother reply: {db_err}")
        except Exception as e:
            logger.warning(f"Could not check conversation status: {e}")
    
    # If mother is addressing doctor but we couldn't find case_discussions (first time),
    # still route to doctor
    if addressing_doctor and not skip_ai_response and mother_id:
        skip_ai_response = True
        sender_role = "doctor"
        logger.info(f"👨‍⚕️ Mother addressing doctor - routing to case_discussions")
        try:
            supabase.table("case_discussions").insert({
                "mother_id": str(mother_id),
                "sender_role": "mother",
                "sender_name": mother.get('name', 'Mother') if mother else 'Mother',
                "message": text,
            }).execute()
            logger.info(f"💬 New doctor conversation started by mother")
        except Exception as db_err:
            logger.error(f"Failed to save mother message: {db_err}")
    
    try:
        await save_chat_history(mother_id, "user_query", text, telegram_chat_id=chat_id)
    except Exception:
        pass
    
    # If doctor/ASHA conversation is active, just acknowledge without AI response
    if skip_ai_response:
        try:
            await update.message.reply_text(
                f"✅ Your message has been sent to your {sender_role.lower()}. They will respond shortly."
            )
        except Exception:
            pass
        return
    
    # Normal AI agent flow with INTELLIGENT MEMORY
    
    # -------------------------------------------------------------
    # FAST-PATH: Gemini Query Caching!
    # If the exact same question was asked recently by anyone, 
    # and no special conversation context is needed, return instantly!
    # -------------------------------------------------------------
    cache_key = text.lower().strip()
    if not skip_ai_response and not is_emergency:
        cached_data = _query_cache.get(cache_key)
        if cached_data:
            reply, ts = cached_data
            if time.time() - ts < CACHE_TTL:
                logger.info(f"⚡ FAST-PATH CACHE HIT! Returning instant answer for: {cache_key[:30]}...")
                try:
                    await update.message.reply_text(reply)
                    await save_chat_history(mother_id, "agent_response", reply, telegram_chat_id=chat_id)
                except Exception:
                    pass
                return
            else:
                del _query_cache[cache_key]
    
    try:
        reports = await get_recent_reports_for_mother(mother.get('id')) if (mother and callable(get_recent_reports_for_mother)) else []
    except Exception:
        reports = []
    
    # Get conversation context with past history for follow-up questions
    conversation_context = None
    extracted_info = {}
    try:
        if CONVERSATION_MEMORY_AVAILABLE:
            mother_name = mother.get('name', '') if mother else ''
            conversation_context = await get_follow_up_context(mother_id, text, mother_name)
            extracted_info = await extract_message_info(text)
            
            if conversation_context and conversation_context.has_history:
                logger.info(f"🧠 Found {len(conversation_context.similar_conversations)} relevant past conversations")
                # Add follow-up context to mother_context for routing
                mother_context['follow_up_prompt'] = conversation_context.follow_up_prompt
                mother_context['past_symptoms'] = conversation_context.past_symptoms
                mother_context['past_advice'] = conversation_context.past_advice
    except Exception as mem_err:
        logger.warning(f"Could not get conversation memory: {mem_err}")
    
    try:
        reply = await route_message(text, mother_context, reports)
        logger.info(f"✅ Agent reply generated successfully for: {text[:50]}")
        
        # Save to fast-path cache if it's a generic educational question
        # (Generic responses usually don't have extremely lengthy context)
        if not conversation_context or not conversation_context.has_history:
            _query_cache[cache_key] = (reply, time.time())
            
            # Prevent memory bloating
            if len(_query_cache) > 2000:
                oldest = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
                del _query_cache[oldest]
                
        # Store conversation for future memory (async, non-blocking)
        try:
            if CONVERSATION_MEMORY_AVAILABLE and extracted_info:
                await save_conversation(
                    mother_id=str(mother_id),
                    messages=[{"role": "user", "content": text}, {"role": "assistant", "content": reply}],
                    topics=extracted_info.get('topics', []),
                    symptoms=extracted_info.get('symptoms', []),
                    advice=reply[:500] if reply else None
                )
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Routing error for message '{text}': {e}", exc_info=True)
        reply = f"I'm having trouble processing that right now. Please try again."
    
    try:
        await update.message.reply_text(clean_for_telegram(reply))
        try:
            await save_chat_history(mother_id, "agent_response", reply, telegram_chat_id=chat_id)
        except Exception:
            pass
    except Exception as reply_error:
        logger.error(f"Error sending reply: {reply_error}", exc_info=True)
        try:
            await update.message.reply_text("I'm here to help. Please try rephrasing your question or use /start for the menu.")
        except Exception:
            pass

