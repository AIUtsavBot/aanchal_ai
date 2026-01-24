# MatruRaksha AI - Telegram API Endpoints

> API endpoints for Telegram bot integration and webhooks

---

## Telegram Webhook

### POST `/telegram/webhook/{token}`
Webhook endpoint for receiving Telegram updates.

**Path Parameters:**
- `token` (string, required): The Telegram bot token for verification

**Request Body:** (Sent by Telegram)
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "is_bot": false,
      "first_name": "User",
      "username": "username"
    },
    "chat": {
      "id": 123456789,
      "first_name": "User",
      "username": "username",
      "type": "private"
    },
    "date": 1704412800,
    "text": "/start"
  }
}
```

**Response:**
```json
{
  "ok": true
}
```

**Error Response:**
```json
{
  "ok": false,
  "error": "Bot not ready"
}
```

---

## Telegram Bot Configuration

### Webhook Mode vs Polling Mode

The bot supports two modes of operation:

#### Webhook Mode (Recommended for Production)
- More efficient - only triggers when messages arrive
- Requires `BACKEND_URL` environment variable
- Set `USE_TELEGRAM_WEBHOOK=true`

#### Polling Mode (Default for Development)
- Bot continuously polls Telegram for updates
- Works without public URL
- Set `USE_TELEGRAM_WEBHOOK=false` or leave `BACKEND_URL` unset

---

## Internal Telegram Service API

These endpoints are used internally by the bot and are not meant for external access.

### Send Alert to Mother
Internal function to send health alerts via Telegram.

**Function:** `telegram_service.send_message(chat_id, message)`

**Parameters:**
- `chat_id`: Telegram chat ID of the mother
- `message`: Markdown-formatted message

---

### Send Emergency Alert
Internal function to notify healthcare providers of emergencies.

**Function:** `telegram_service.send_emergency_alert(mother_id, alert_type, details)`

**Parameters:**
- `mother_id`: UUID of the mother
- `alert_type`: Type of emergency (HIGH_RISK, EMERGENCY, etc.)
- `details`: Additional context about the emergency

---

## Telegram Bot Callback Data

The bot uses callback queries for interactive buttons. Here are the callback patterns:

| Pattern | Description |
|---------|-------------|
| `register` | Start registration flow |
| `register_new` | Register additional mother |
| `switch_mother_{id}` | Switch active mother profile |
| `action_summary` | View health summary |
| `action_upload` | Upload medical document |
| `action_checkin` | Daily check-in |
| `action_alert` | Send emergency alert |
| `lang_{code}` | Select language (en/hi/mr) |
| `confirm_yes` | Confirm registration |
| `confirm_no` | Cancel registration |

---

## Telegram Update Types Handled

The bot processes the following update types:

1. **Commands**
   - `/start` - Initialize bot and show dashboard
   - `/cancel` - Cancel current operation

2. **Messages**
   - Text messages (for registration flow and queries)
   - Documents (PDF uploads for analysis)
   - Photos (medical report images)

3. **Callback Queries**
   - Button interactions
   - Navigation between screens

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes |
| `BACKEND_URL` | Public URL for webhooks | For webhook mode |
| `USE_TELEGRAM_WEBHOOK` | Enable webhook mode | No (default: true) |

---

*Last updated: January 2026*
