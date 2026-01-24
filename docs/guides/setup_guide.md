# MatruRaksha AI - Setup Guide

> Step-by-step guide to set up the MatruRaksha Maternal Health Monitoring System locally

---

## Prerequisites

Before starting, ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12+ | Backend runtime |
| **Node.js** | 20+ | Frontend build tools |
| **npm** | 10+ | Package management |
| **Git** | Latest | Version control |

---

## Quick Start (5 minutes)

```powershell
# 1. Clone the repository
git clone https://github.com/your-org/MatruRaksha_AI_Event.git
cd MatruRaksha_AI_Event

# 2. Backend setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows
# source venv/bin/activate           # Linux/Mac
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your credentials

# 4. Start backend
python main.py

# 5. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

---

## Detailed Setup Instructions

### Step 1: Clone the Repository

```powershell
git clone https://github.com/your-org/MatruRaksha_AI_Event.git
cd MatruRaksha_AI_Event
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables

Copy the example environment file:
```powershell
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/Mac
```

Edit `.env` with your actual credentials:

```env
# Required: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Required: Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# Recommended: AI Analysis
GEMINI_API_KEY=your-gemini-api-key

# Optional: Webhooks (for production)
BACKEND_URL=http://localhost:8000
```

#### 2.4 Start the Backend

```bash
python main.py
```

You should see:
```
============================================================
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║           🤰 MatruRaksha AI System 🤰           ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
============================================================
✅ Supabase client initialized
✅ Gemini AI initialized
✅ AI Agents loaded successfully
🤖 MatruRaksha Telegram Bot is ACTIVE
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 3: Frontend Setup

Open a **new terminal** window.

#### 3.1 Install Dependencies

```bash
cd frontend
npm install
```

#### 3.2 Configure Environment

Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

#### 3.3 Start the Frontend

```bash
npm run dev
```

You should see:
```
  VITE v7.1.10  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  press h + enter to show help
```

---

## External Service Setup

### 1. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **Settings** > **API**
3. Copy the following:
   - Project URL (`SUPABASE_URL`)
   - `anon` public key (`SUPABASE_KEY`)
   - `service_role` key (`SUPABASE_SERVICE_ROLE_KEY`)

4. Run the database schema:
   - Go to **SQL Editor**
   - Paste the contents of `infra/supabase/schema.sql`
   - Click **Run**

5. Create storage buckets:
   - Go to **Storage**
   - Create bucket: `medical-reports` (public)
   - Create bucket: `documents` (public)

---

### 2. Telegram Bot Setup

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts to create your bot
4. Copy the bot token to `TELEGRAM_BOT_TOKEN`

**Test your bot:**
- Search for your bot in Telegram
- Send `/start`
- You should see the welcome message

---

### 3. Google Gemini AI Setup

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **Get API Key**
3. Create a new API key
4. Copy to `GEMINI_API_KEY`

---

### 4. Email Notifications (Optional)

For email alerts, configure Resend:

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Add to `.env`:
   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxx
   FROM_EMAIL=noreply@yourdomain.com
   ```

---

## Verification Checklist

After setup, verify everything works:

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "supabase_connected": true,
  "telegram_bot_token": "✅ Set",
  "telegram_polling": "🟢 Active",
  "gemini_ai": "🤖 Active"
}
```

### Frontend Check
- Open http://localhost:5173
- You should see the MatruRaksha landing page
- Login and Signup buttons should be visible

### Telegram Bot Check
- Search for your bot in Telegram
- Send `/start`
- You should see a welcome message with registration options

---

## Troubleshooting

### Common Issues

#### 1. `ModuleNotFoundError`
```bash
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Telegram Bot Not Responding
- Check `TELEGRAM_BOT_TOKEN` is correct
- Ensure no other instance is polling (one bot = one instance)
- Check logs for `🤖 MatruRaksha Telegram Bot is ACTIVE`

#### 3. Supabase Connection Failed
- Verify `SUPABASE_URL` starts with `https://`
- Verify `SUPABASE_KEY` is the `anon` key (not `service_role`)
- Check if project is paused (free tier pauses after inactivity)

#### 4. CORS Errors on Frontend
- Ensure backend is running on port 8000
- Check `VITE_API_URL` matches backend URL
- Clear browser cache

#### 5. Gemini AI Not Working
- Verify `GEMINI_API_KEY` is valid
- Check Google AI Studio quota
- The system works without AI (manual analysis required)

---

## Running Both Services Together

**Option 1: Two Terminal Windows**
```powershell
# Terminal 1 - Backend
cd backend
.\venv\Scripts\Activate.ps1
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option 2: Using Docker Compose**
```powershell
cd infra/docker
docker-compose up -d
```

---

## Next Steps

After setup is complete:

1. 📖 Read the [API Documentation](../api/endpoints.md)
2. 🤖 Explore [Telegram Bot Commands](../telegram/bot_commands.md)
3. 🚀 Check the [Deployment Guide](./deployment_guide.md)
4. 🏗️ Review the [System Architecture](../architecture/system_design.md)

---

*Last updated: January 2026*
