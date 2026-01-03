# 🚀 MatruRaksha Setup Guide

> Complete step-by-step guide to set up the MatruRaksha AI maternal health monitoring system for local development.

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Detailed Setup](#-detailed-setup)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Supabase Setup](#2-supabase-setup)
  - [3. Backend Setup](#3-backend-setup)
  - [4. Frontend Setup](#4-frontend-setup)
  - [5. Telegram Bot Setup](#5-telegram-bot-setup)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [Verification Steps](#-verification-steps)
- [Troubleshooting](#-troubleshooting)

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20.19+ | [nodejs.org](https://nodejs.org/) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

**Accounts Required:**
- [Supabase](https://supabase.com/) - Database and Auth (Free tier available)
- [Telegram](https://telegram.org/) - For creating a bot
- [Google Cloud Console](https://console.cloud.google.com/) - For OAuth (optional)
- [Resend](https://resend.com/) - Email notifications (Free tier available)
- [Google AI Studio](https://makersuite.google.com/) - Gemini API key

---

## ⚡ Quick Start

For experienced developers, here's the quick setup:

```bash
# Clone and setup backend
git clone https://github.com/yourusername/matruraksha-ai.git
cd matruraksha-ai/backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env     # Edit with your credentials

# Setup frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env.local  # Edit with your credentials

# Run (two terminals)
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## 📝 Detailed Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/matruraksha-ai.git
cd matruraksha-ai
```

**Repository Structure:**
```
matruraksha-ai/
├── backend/          # FastAPI Python backend
├── frontend/         # React Vite frontend
├── docs/             # Documentation
├── infra/            # Infrastructure configs
├── README.md
└── CHANGELOG.md
```

---

### 2. Supabase Setup

#### 2.1 Create a Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. Enter:
   - Project name: `matruraksha`
   - Database password: (save this securely)
   - Region: Choose closest to your users

4. Wait for project to initialize (~2 minutes)

#### 2.2 Get API Keys

Navigate to **Settings > API** and copy:

- **Project URL:** `https://xxxxx.supabase.co`
- **anon/public key:** `eyJhbGciOiJIUzI1NiIs...`
- **service_role key:** `eyJhbGciOiJIUzI1NiIs...` (keep secret!)

#### 2.3 Run Database Migrations

1. Go to **SQL Editor** in Supabase Dashboard
2. Open `infra/supabase/schema.sql` from the repo
3. Copy and paste the entire content
4. Click **Run**

This creates all required tables:
- `mothers`, `doctors`, `asha_workers`
- `risk_assessments`, `medical_reports`
- `user_profiles`, `registration_requests`
- And all indexes, triggers, RLS policies

#### 2.4 Enable Google OAuth (Optional)

1. Go to **Authentication > Providers**
2. Enable **Google**
3. Configure with your Google Cloud OAuth credentials
4. Add redirect URL to Google Console: `https://xxxxx.supabase.co/auth/v1/callback`

#### 2.5 Create Storage Bucket

1. Go to **Storage** in Supabase
2. Click **New Bucket**
3. Name: `documents`
4. Check "Public bucket"
5. Click **Create**

---

### 3. Backend Setup

#### 3.1 Create Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

#### 3.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3.3 Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BACKEND_API_BASE_URL=http://localhost:8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini-2.5-flash

# Email (Resend)
RESEND_API_KEY=re_xxxx
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=MatruRaksha AI

# Security
PASSWORD_ENCRYPTION_KEY=your_secure_random_key
```

#### 3.4 Verify Setup

```bash
python verify_setup.py
```

This checks all environment variables and database connectivity.

---

### 4. Frontend Setup

#### 4.1 Install Node Dependencies

```bash
cd frontend
npm install
```

> **Note:** If you see errors about Node version, ensure you're using Node 20.19+

#### 4.2 Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
VITE_TELEGRAM_BOT_NAME=YourBotName
```

---

### 5. Telegram Bot Setup

#### 5.1 Create a Bot with BotFather

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow prompts:
   - Bot name: `MatruRaksha Health Bot`
   - Username: `matruraksha_bot` (must end with `_bot`)
4. Copy the **API token**
5. Add to `backend/.env` as `TELEGRAM_BOT_TOKEN`

#### 5.2 Set Bot Commands (Optional)

Send to BotFather:
```
/setcommands
```

Then paste:
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

## 🔧 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key (admin ops) |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token from BotFather |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `FRONTEND_URL` | ✅ | Frontend URL for CORS (e.g., `http://localhost:5173`) |
| `RESEND_API_KEY` | ⬜ | Resend API key for emails |
| `PASSWORD_ENCRYPTION_KEY` | ⬜ | Key for encrypting registration passwords |
| `FAST2SMS_API_KEY` | ⬜ | Fast2SMS key for SMS (India) |
| `VAPI_API_KEY` | ⬜ | Vapi.ai key for voice calls |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_SUPABASE_URL` | ✅ | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `VITE_API_URL` | ✅ | Backend API URL |
| `VITE_TELEGRAM_BOT_NAME` | ⬜ | Telegram bot username (without @) |

---

## 🏃 Running the Application

### Start Backend

```bash
cd backend
.\venv\Scripts\activate  # Windows
python main.py
```

Backend runs at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: **http://localhost:5173**

### Start Scheduler (Optional)

For automated tasks like daily reminders:

```bash
cd backend
python scheduler.py

# Or test mode (immediate execution):
python scheduler.py test
```

---

## ✅ Verification Steps

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Check Frontend

Open http://localhost:5173 in your browser.

### 3. Test Telegram Bot

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Note your Chat ID

### 4. Register a Test Mother

```bash
curl -X POST http://localhost:8000/mothers/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Mother",
    "phone": "9876543210",
    "age": 28,
    "location": "Mumbai"
  }'
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Module not found" error in Python

```bash
pip install -r requirements.txt
```

#### 2. "crypto.hash is not a function" in Frontend

Upgrade Node.js to v20.19+:
```bash
nvm install 20
nvm use 20
```

#### 3. CORS errors

Ensure `FRONTEND_URL` in backend `.env` matches your frontend URL exactly.

#### 4. Supabase connection failed

- Check `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Verify your IP isn't blocked in Supabase settings

#### 5. Telegram bot not responding

- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check bot is not blocked by user
- Ensure backend is running

### Getting Help

1. Check [GitHub Issues](https://github.com/yourusername/matruraksha-ai/issues)
2. Review error logs
3. Open a new issue with:
   - Error message
   - Steps to reproduce
   - Environment (OS, Python version, Node version)

---

## 📚 Next Steps

After setup, you can:

1. **Create an Admin User** - Insert directly into `user_profiles` table
2. **Configure Email Templates** - Customize in `backend/services/email_service.py`
3. **Deploy to Production** - See [Deployment Guide](./deployment_guide.md)
4. **Integrate Voice Calls** - Configure Vapi.ai settings

---

*Last Updated: January 2026*
