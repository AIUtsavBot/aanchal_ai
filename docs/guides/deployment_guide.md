# 🚀 MatruRaksha Deployment Guide

> Complete guide for deploying MatruRaksha AI to production environments.

---

## 📋 Table of Contents

- [Deployment Options](#-deployment-options)
- [Recommended Stack](#-recommended-stack)
- [Vercel Deployment (Frontend)](#-vercel-deployment-frontend)
- [Render Deployment (Backend)](#-render-deployment-backend)
- [Docker Deployment](#-docker-deployment)
- [Environment Configuration](#-environment-configuration)
- [Database Setup](#-database-setup)
- [Post-Deployment Checklist](#-post-deployment-checklist)
- [Monitoring & Maintenance](#-monitoring--maintenance)

---

## 🎯 Deployment Options

| Platform | Component | Pros | Cons |
|----------|-----------|------|------|
| **Vercel** | Frontend | Free tier, automatic deploys, global CDN | Limited to frontend |
| **Render** | Backend | Free tier, easy setup, auto-deploy | Cold starts on free tier |
| **Railway** | Backend | Simple, good for FastAPI | Limited free tier |
| **Fly.io** | Backend | Global edge, Docker support | More complex setup |
| **Docker** | Both | Full control, reproducible | Requires infrastructure |
| **AWS/GCP** | Both | Enterprise-grade | Complex, expensive |

---

## ✨ Recommended Stack

For most use cases, we recommend:

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION STACK                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Frontend: Vercel (Free)                                   │
│   ├── Automatic deploys from GitHub                         │
│   ├── Global CDN                                             │
│   └── HTTPS included                                         │
│                                                              │
│   Backend: Render (Free/Paid)                               │
│   ├── FastAPI auto-detection                                │
│   ├── Environment variables UI                              │
│   └── Health checks                                          │
│                                                              │
│   Database: Supabase (Free)                                 │
│   ├── PostgreSQL managed                                    │
│   ├── Auth included                                         │
│   └── Storage for files                                     │
│                                                              │
│   Telegram Bot: Runs on Render backend                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔷 Vercel Deployment (Frontend)

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Import your GitHub repository
4. Select the `frontend` folder as Root Directory

### Step 2: Configure Build Settings

| Setting | Value |
|---------|-------|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

### Step 3: Environment Variables

Add in Vercel Dashboard → Settings → Environment Variables:

```
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
VITE_API_URL=https://your-backend.onrender.com
VITE_TELEGRAM_BOT_NAME=matruraksha_bot
```

### Step 4: Deploy

Click **Deploy** and wait for the build to complete.

### Step 5: Configure `vercel.json`

Create/update `frontend/vercel.json` for SPA routing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 🔶 Render Deployment (Backend)

### Step 1: Connect Repository

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the `backend` folder

### Step 2: Configure Service

| Setting | Value |
|---------|-------|
| Name | `matruraksha-backend` |
| Region | Choose closest to users |
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### Step 3: Environment Variables

Add in Render Dashboard → Environment:

```
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
BACKEND_API_BASE_URL=https://your-backend.onrender.com

# Frontend CORS
FRONTEND_URL=https://your-frontend.vercel.app

# AI
GEMINI_API_KEY=your_gemini_key

# Email
RESEND_API_KEY=re_xxxx
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=MatruRaksha AI

# Security
PASSWORD_ENCRYPTION_KEY=your_secure_key
```

### Step 4: Deploy

Click **Create Web Service** and wait for deployment.

### Step 5: Optional - `render.yaml`

For Infrastructure as Code, create `render.yaml` in repo root:

```yaml
services:
  - type: web
    name: matruraksha-backend
    env: python
    region: singapore
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      # Add other env vars...
```

---

## 🐳 Docker Deployment

### Backend Dockerfile

Located at `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Located at `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - FRONTEND_URL=http://localhost:3000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### Run with Docker Compose

```bash
# Create .env file with all variables
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🔧 Environment Configuration

### Production Checklist

- [ ] All API keys are production keys (not test)
- [ ] `FRONTEND_URL` matches your deployed frontend domain
- [ ] `BACKEND_API_BASE_URL` matches your deployed backend URL
- [ ] Google OAuth redirect URLs updated in Supabase and Google Console
- [ ] Telegram bot webhook set to production URL

### Setting Telegram Webhook

After backend deployment:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-backend.onrender.com/telegram/webhook"}'
```

---

## 🗄️ Database Setup

### Production Supabase Configuration

1. **Enable Row Level Security** on all tables
2. **Create indexes** for performance (already in schema.sql)
3. **Enable Realtime** for case_discussions table
4. **Configure Storage** bucket policies

### Backup Strategy

```sql
-- Enable point-in-time recovery in Supabase Pro
-- Or export manually:
pg_dump -h db.xxxxx.supabase.co -U postgres -d postgres > backup.sql
```

---

## ✅ Post-Deployment Checklist

### Backend Verification

```bash
# Health check
curl https://your-backend.onrender.com/health

# API docs accessible
# Visit: https://your-backend.onrender.com/docs
```

### Frontend Verification

1. Open deployed frontend URL
2. Test Google OAuth login
3. Verify API calls work (no CORS errors)
4. Test all dashboards with real data

### Telegram Bot Verification

1. Send `/start` to your bot
2. Complete registration flow
3. Test health check-in

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS errors | Ensure `FRONTEND_URL` matches exactly |
| OAuth redirect fails | Update URLs in Supabase Auth settings |
| Bot not responding | Check webhook is set correctly |
| Slow cold starts | Upgrade to paid tier or use health checks |

---

## 📊 Monitoring & Maintenance

### Health Monitoring

Set up uptime monitoring with:
- [UptimeRobot](https://uptimerobot.com/) (Free)
- [Better Uptime](https://betteruptime.com/)
- [Render Health Checks](https://render.com/docs/health-checks)

**Health Check Endpoint:** `GET /health`

### Logging

Access logs via:
- **Render:** Dashboard → Logs
- **Vercel:** Dashboard → Functions → Logs
- **Docker:** `docker-compose logs -f`

### Performance Monitoring

- Built-in caching reduces DB load (30s TTL)
- Monitor Supabase usage in dashboard
- Set up alerts for high-risk patient notifications

### Updates & Maintenance

```bash
# Pull latest code
git pull origin main

# Redeploy
# - Vercel: Automatic on push
# - Render: Automatic on push or manual trigger
# - Docker: docker-compose up -d --build
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` files**
2. **Use environment variables** for all secrets
3. **Enable HTTPS** (automatic on Vercel/Render)
4. **Rotate API keys** periodically
5. **Monitor for unusual activity**
6. **Keep dependencies updated**

---

## 📚 Related Documentation

- [Setup Guide](./setup_guide.md)
- [System Design](../architecture/system_design.md)
- [API Endpoints](../api/endpoints.md)

---

*Last Updated: January 2026*
