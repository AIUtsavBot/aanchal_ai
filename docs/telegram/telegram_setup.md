# MatruRaksha AI - Telegram Bot Setup

> Guide to create and configure your Telegram bot for MatruRaksha

---

## Part 1: Creating the Bot

### Step 1: Find BotFather

1. Open Telegram app (mobile or desktop)
2. Search for **@BotFather**
3. Start a chat with BotFather

![BotFather Search](https://core.telegram.org/img/botfather.jpg)

### Step 2: Create New Bot

Send the following command:
```
/newbot
```

BotFather will ask:
```
Alright, a new bot. How are we going to call it?
Please choose a name for your bot.
```

Enter a name:
```
MatruRaksha AI
```

BotFather will ask:
```
Good. Now let's choose a username for your bot.
It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.
```

Enter a username:
```
MatruRakshaBot
```

> **Note**: The username must be unique across all of Telegram

### Step 3: Get Your Token

BotFather will respond with:
```
Done! Congratulations on your new bot. You will find it at t.me/MatruRakshaBot.
You can now add a description, about section and profile picture for your bot.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

Keep your token secure and store it safely.
```

**Copy this token** - you'll need it for configuration!

---

## Part 2: Bot Configuration

### Set Bot Description

```
/setdescription
```

Enter a description:
```
🤰 AI-powered maternal health monitoring system.

I help pregnant mothers:
• Track health metrics
• Analyze medical reports
• Get AI health guidance
• Connect with healthcare providers

Start with /start to register!
```

### Set About Text

```
/setabouttext
```

Enter:
```
MatruRaksha AI - Your 24/7 maternal health companion.

Developed for mothers in low-resource settings in India.
```

### Set Bot Profile Picture

```
/setuserpic
```

Upload a suitable logo/image for your bot.

### Set Bot Commands Menu

```
/setcommands
```

Enter:
```
start - Start the bot and show dashboard
cancel - Cancel current operation
```

---

## Part 3: Backend Configuration

### Add Token to Environment

Add your bot token to `backend/.env`:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
```

### Development Mode (Polling)

For local development, use polling mode:

```env
USE_TELEGRAM_WEBHOOK=false
```

The bot will automatically poll Telegram for updates.

### Production Mode (Webhooks)

For production, use webhooks for efficiency:

```env
USE_TELEGRAM_WEBHOOK=true
BACKEND_URL=https://your-backend.onrender.com
```

The backend will automatically configure the webhook on startup.

---

## Part 4: Verify Bot Setup

### Start the Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

Look for these log messages:
```
🤖 Initializing Telegram Bot in background thread...
✅ Telegram Bot initialized successfully
🚀 Starting Telegram polling...
✅ Telegram polling started
🤖 MatruRaksha Telegram Bot is ACTIVE (polling mode)
```

### Test the Bot

1. Open Telegram
2. Search for your bot username
3. Click **Start** or send `/start`
4. You should see the welcome message:

```
🤰 Welcome to MatruRaksha AI!

Your 24/7 maternal health companion.

What would you like to do?

[📝 Register Mother] [📊 View Dashboard]
```

---

## Part 5: Troubleshooting

### Bot Not Responding

**Check 1: Token is correct**
```python
# In Python, test your token
import requests
token = "YOUR_TOKEN"
response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print(response.json())
```

**Check 2: Only one instance running**
- Telegram only allows one bot instance at a time
- Kill other instances before starting

**Check 3: Check error logs**
```
Look for: ❌ Error in Telegram bot:
```

### Webhook Issues

**Verify webhook is set:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Clear webhook (to use polling):**
```bash
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

**Set webhook manually:**
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-backend.com/telegram/webhook/<TOKEN>"}'
```

### Conflicting Instances

If you see:
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request
```

This means another instance is polling. Solutions:
1. Stop other instances
2. Wait 10 seconds, then restart
3. Use webhooks instead of polling

---

## Part 6: Advanced Configuration

### Inline Mode (Optional)

Enable inline queries:
```
/setinline
```

Enter placeholder text:
```
Search for health information...
```

### Privacy Mode

By default, bots in groups only see messages starting with `/` or mentioning the bot.

To change this:
```
/setprivacy
```

Select **Disable** to see all messages (if needed for group features).

### Domain Linking

If you have a website:
```
/setdomain
```

Enter your domain for better user experience.

---

## Part 7: Bot Maintenance

### Update Bot Token

If your token is compromised:
1. Go to BotFather
2. Send `/revoke`
3. Select your bot
4. A new token will be generated
5. Update your `.env` file

### Delete Bot

To permanently delete:
```
/deletebot
```

Select your bot and confirm.

### Transfer Ownership

BotFather currently doesn't support ownership transfer. Create a new bot if needed.

---

## Security Best Practices

1. **Never share your token** publicly
2. **Don't commit token** to git (use `.env` files)
3. **Use webhooks** in production for security
4. **Validate webhook requests** (the backend does this automatically)
5. **Rotate token** if you suspect it's compromised

---

## Useful BotFather Commands

| Command | Description |
|---------|-------------|
| `/mybots` | List your bots |
| `/setname` | Change bot display name |
| `/setdescription` | Set bot description |
| `/setabouttext` | Set about text |
| `/setuserpic` | Set profile picture |
| `/setcommands` | Set command menu |
| `/deletebot` | Delete a bot |
| `/revoke` | Generate new token |
| `/setinline` | Enable inline mode |
| `/setprivacy` | Set privacy mode |

---

## Next Steps

After setup:
1. 📖 Read [Bot Commands Reference](./bot_commands.md)
2. 🔧 Configure backend with [Setup Guide](../guides/setup_guide.md)
3. 🚀 Deploy with [Deployment Guide](../guides/deployment_guide.md)

---

*Last updated: January 2026*
