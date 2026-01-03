# 📱 Telegram Bot Setup Guide

> Complete guide to setting up and configuring the MatruRaksha Telegram bot.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Creating the Bot](#-creating-the-bot)
- [Configuration](#-configuration)
- [Webhook Setup](#-webhook-setup)
- [Testing](#-testing)
- [Customization](#-customization)
- [Troubleshooting](#-troubleshooting)

---

## 🔍 Overview

The MatruRaksha Telegram bot provides 24/7 maternal health support through:

- **Daily Health Check-ins** - Automated morning reminders
- **AI-Powered Consultations** - Gemini-powered health advice
- **Document Analysis** - Upload and analyze medical reports
- **Emergency Detection** - Automatic alerts for danger signs
- **Multilingual Support** - Coming soon

**Architecture:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mother    │────▶│  Telegram   │────▶│  MatruRaksha│
│  (Telegram) │     │   Servers   │     │   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ Webhook
                          ▼
                    ┌─────────────┐
                    │  telegram_  │
                    │  bot.py     │
                    └─────────────┘
```

---

## 🤖 Creating the Bot

### Step 1: Open BotFather

1. Open Telegram on your phone or desktop
2. Search for `@BotFather`
3. Start a chat and send `/start`

### Step 2: Create New Bot

Send the command:
```
/newbot
```

### Step 3: Name Your Bot

BotFather will ask for:

**1. Display Name (shown in chats):**
```
MatruRaksha Health Bot
```

**2. Username (must end with `bot` or `_bot`):**
```
matruraksha_bot
```

### Step 4: Copy Bot Token

BotFather will respond with:
```
Done! Congratulations on your new bot. You will find it at t.me/matruraksha_bot.

Use this token to access the HTTP API:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz

Keep your token secure and store it safely.
```

**⚠️ Important:** Keep this token secret! Never commit it to version control.

### Step 5: Save Token

Add to your `backend/.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## ⚙️ Configuration

### Basic Configuration

In `backend/.env`:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
BACKEND_API_BASE_URL=http://localhost:8000

# For production:
# BACKEND_API_BASE_URL=https://your-backend.onrender.com
```

### Bot Settings via BotFather

#### Set Bot Description
```
/setdescription
```
Then select your bot and enter:
```
🤰 MatruRaksha AI - Your 24/7 maternal health companion

✨ Features:
• Daily health check-ins
• AI-powered health advice
• Medical report analysis
• Emergency alerts

Start with /register to begin your health journey.
```

#### Set Bot About Text
```
/setabouttext
```
Enter:
```
AI-powered maternal health monitoring for pregnant mothers in underserved communities. Developed by MatruRaksha AI team.
```

#### Set Bot Profile Picture
```
/setuserpic
```
Then send a 512x512 image of your logo.

#### Set Bot Commands
```
/setcommands
```
Select your bot and paste:
```
start - Start the bot and get your chat ID
register - Register a new mother profile
checkin - Daily health check-in
status - View current health status
timeline - View health history
report - Report symptoms or concerns
help - Show available commands
cancel - Cancel current operation
```

---

## 🔗 Webhook Setup

### Development (Polling)

For local development, the bot uses polling (no webhook needed):

```python
# In telegram_bot.py - already configured
application.run_polling()
```

### Production (Webhook)

For production, set up webhook for better performance:

#### 1. Set Webhook URL

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-backend.onrender.com/telegram/webhook",
    "allowed_updates": ["message", "callback_query"]
  }'
```

Expected response:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

#### 2. Verify Webhook

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

#### 3. Delete Webhook (if needed)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

### Webhook vs Polling

| Feature | Polling | Webhook |
|---------|---------|---------|
| Setup | Automatic | Manual |
| Latency | Higher | Lower |
| Server Load | Higher | Lower |
| SSL Required | No | Yes |
| Use Case | Development | Production |

---

## 🧪 Testing

### Test Bot Locally

1. Start the backend:
```bash
cd backend
python main.py
```

2. Open Telegram and message your bot:
```
/start
```

3. Note your Chat ID from the response

### Test Registration

```bash
curl -X POST http://localhost:8000/mothers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Mother",
    "phone": "9876543210",
    "age": 28,
    "location": "Mumbai",
    "telegram_chat_id": "YOUR_CHAT_ID"
  }'
```

### Test Sending Message

```bash
curl -X POST http://localhost:8000/telegram/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID",
    "message": "Hello from MatruRaksha API!"
  }'
```

### Test Emergency Alert

```bash
curl -X POST http://localhost:8000/telegram/send-alert \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID",
    "alert_type": "test",
    "message": "This is a test emergency alert"
  }'
```

---

## 🎨 Customization

### Custom Keyboard Layouts

Edit in `backend/telegram_bot.py`:

```python
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

# Reply Keyboard (appears below text input)
main_menu = ReplyKeyboardMarkup([
    ["📋 Check-in", "📊 Status"],
    ["📅 Timeline", "🏥 Report"],
    ["❓ Help"]
], resize_keyboard=True)

# Inline Keyboard (appears in message)
risk_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("View Details", callback_data="view_risk")],
    [InlineKeyboardButton("Contact Doctor", callback_data="contact_doctor")]
])
```

### Custom Messages

Edit message templates in `backend/telegram_bot.py`:

```python
MESSAGES = {
    "welcome": """
🙏 Welcome to MatruRaksha AI!

I'm your maternal health companion. I'm here to help you through 
your pregnancy journey.

Your Chat ID: {chat_id}
    """,
    
    "checkin_start": """
🌅 Good morning, {name}!
How are you feeling today?
    """,
    
    "emergency": """
🚨 EMERGENCY ALERT 🚨

{symptoms} detected.
Please seek immediate medical attention.

📞 Ambulance: 108
📞 Doctor: {doctor_phone}
    """
}
```

### Adding New Commands

```python
# In telegram_bot.py

async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mycommand"""
    chat_id = update.effective_chat.id
    await update.message.reply_text("Hello! This is my new command.")

# Register handler
application.add_handler(CommandHandler("mycommand", new_command))
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Not Responding

**Symptoms:** Messages sent to bot get no response

**Solutions:**
- Check backend is running: `curl http://localhost:8000/health`
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check for Python errors in console
- Ensure bot is not blocked by user

#### 2. Webhook Returns 404

**Symptoms:** Telegram shows "Webhook failed" error

**Solutions:**
- Verify webhook URL is correct
- Check backend is publicly accessible
- Ensure HTTPS is enabled
- Check `/telegram/webhook` route exists

#### 3. "Conflict: terminated by other getUpdates request"

**Symptoms:** Error when running bot

**Solutions:**
- Only run one instance of the bot
- Delete webhook if using polling
- Check for duplicate processes

#### 4. Messages Delayed

**Symptoms:** Bot responds slowly

**Solutions:**
- Check AI service (Gemini) connectivity
- Reduce database query complexity
- Enable caching
- Use webhook instead of polling

### Debug Mode

Enable detailed logging:

```python
# In telegram_bot.py
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
```

### Check Bot Status

```python
import requests

token = "YOUR_BOT_TOKEN"

# Get bot info
response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print(response.json())

# Get updates
response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
print(response.json())

# Get webhook info
response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print(response.json())
```

---

## 🔒 Security Best Practices

1. **Never expose bot token** - Use environment variables
2. **Validate webhook requests** - Check secret token
3. **Rate limit requests** - Prevent abuse
4. **Sanitize user input** - Prevent injection attacks
5. **Log suspicious activity** - Monitor for abuse

### Webhook Secret Token

```python
# Set secret token
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-backend.com/telegram/webhook" \
  -d "secret_token=your_secret_token"

# Verify in webhook handler
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != os.getenv("TELEGRAM_WEBHOOK_SECRET"):
        raise HTTPException(status_code=403, detail="Invalid secret token")
    # Process update...
```

---

## 📊 Analytics & Monitoring

### Track Bot Usage

```python
# Log all incoming messages
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    timestamp = datetime.now()
    
    # Log to database
    await supabase.table("bot_analytics").insert({
        "user_id": user_id,
        "message": message,
        "timestamp": timestamp
    }).execute()
```

### Monitor Health

Set up alerts for:
- Bot response time > 5 seconds
- Error rate > 1%
- Daily active users drop > 20%

---

## 📚 Related Documentation

- [Bot Commands Reference](./bot_commands.md)
- [Telegram API Endpoints](../api/telegram_endpoints.md)
- [Deployment Guide](../guides/deployment_guide.md)

---

*Last Updated: January 2026*
