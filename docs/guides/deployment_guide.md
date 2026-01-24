# MatruRaksha AI - Deployment Guide

> Production deployment instructions for Vercel, Render, and Docker

---

## Deployment Overview

| Component | Platform | URL Format |
|-----------|----------|------------|
| **Frontend** | Vercel | `https://your-app.vercel.app` |
| **Backend** | Render | `https://your-app.onrender.com` |
| **Database** | Supabase | `https://your-project.supabase.co` |

---

## 1. Vercel Deployment (Frontend)

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New** > **Project**
3. Import your GitHub repository
4. Select **Frontend** as the root directory

### Step 2: Configure Build Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### Step 3: Set Environment Variables

In Vercel Project Settings > Environment Variables:

```
VITE_API_URL=https://your-backend.onrender.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Step 4: Deploy

Click **Deploy**. Vercel will automatically deploy on every push to `main`.

### vercel.json Configuration

The project includes a `vercel.json` for SPA routing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

---

## 2. Render Deployment (Backend)

### Step 1: Create New Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New** > **Web Service**
3. Connect your GitHub repository

### Step 2: Configure Service

| Setting | Value |
|---------|-------|
| **Name** | matruraksha-backend |
| **Region** | Singapore (or closest to users) |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT` |

### Step 3: Set Environment Variables

In Render Dashboard > Environment:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Server Configuration
FASTAPI_ENV=production
LOG_LEVEL=INFO
BACKEND_URL=https://your-backend.onrender.com
FRONTEND_URL=https://your-frontend.vercel.app

# Telegram Webhook (recommended for production)
USE_TELEGRAM_WEBHOOK=true

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# OAuth
OAUTH_REDIRECT_URL=https://your-frontend.vercel.app/auth/callback

# Optional
RESEND_API_KEY=your-resend-key
PASSWORD_ENCRYPTION_KEY=your-encryption-key
```

### Step 4: Deploy

Click **Create Web Service**. Render will deploy automatically.

### render.yaml Configuration

The project includes `render.yaml` for infrastructure as code:

```yaml
services:
  - type: web
    name: matruraksha-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
```

---

## 3. Supabase Configuration

### Production Settings

1. **Enable RLS**: Ensure Row Level Security is enabled on all tables
2. **Configure Auth**:
   - Site URL: `https://your-frontend.vercel.app`
   - Redirect URLs: `https://your-frontend.vercel.app/auth/callback`

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs:
   - `https://your-project.supabase.co/auth/v1/callback`
4. In Supabase Dashboard > Authentication > Providers:
   - Enable Google
   - Add Client ID and Secret

### Database Migrations

Run production schema migrations:
```sql
-- Run infra/supabase/schema.sql in Supabase SQL Editor
```

---

## 4. Docker Deployment

### Using Docker Compose

```bash
cd infra/docker

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

Create `.env` file in `backend/` before building:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
# ... other variables
```

### Individual Docker Builds

**Frontend:**
```bash
docker build -f infra/docker/Dockerfile.frontend -t matruraksha-frontend .
docker run -p 80:80 matruraksha-frontend
```

**Backend:**
```bash
docker build -f infra/docker/Dockerfile.backend -t matruraksha-backend .
docker run -p 8000:8000 --env-file backend/.env matruraksha-backend
```

---

## 5. Telegram Webhook Configuration

For production, use webhooks instead of polling:

### Automatic Setup
Set these environment variables on Render:
```env
USE_TELEGRAM_WEBHOOK=true
BACKEND_URL=https://your-app.onrender.com
```

The backend will automatically configure the webhook on startup.

### Manual Webhook Setup
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-backend.onrender.com/telegram/webhook/<YOUR_TOKEN>"}'
```

### Verify Webhook
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

---

## 6. Post-Deployment Checklist

### Health Checks

**Backend:**
```bash
curl https://your-backend.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "supabase_connected": true,
  "telegram_polling": "🟢 Active",
  "gemini_ai": "🤖 Active"
}
```

**Frontend:**
- Visit https://your-app.vercel.app
- Verify login/signup works
- Test Google OAuth flow

**Telegram:**
- Send `/start` to your bot
- Verify registration flow works

### CORS Configuration

Ensure frontend URLs are in backend CORS settings (`main.py`):
```python
ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",
]
```

---

## 7. Custom Domain Setup

### Vercel (Frontend)
1. Go to Project Settings > Domains
2. Add your domain
3. Update DNS records as instructed

### Render (Backend)
1. Go to Service Settings > Custom Domains
2. Add your API subdomain (e.g., `api.yourdomain.com`)
3. Update DNS CNAME to Render's host

### Update Environment Variables
After adding custom domains:
```env
# Frontend
VITE_API_URL=https://api.yourdomain.com

# Backend
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

---

## 8. Monitoring & Logging

### Render Logs
```bash
# View recent logs
render logs --service matruraksha-backend
```

### Vercel Logs
1. Go to Vercel Dashboard
2. Select your project
3. Click **Functions** tab for serverless logs

### Error Tracking (Optional)
Consider adding Sentry for error tracking:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

---

## 9. Scaling Considerations

### Render Scaling
- Upgrade to paid plan for more resources
- Enable auto-scaling for variable traffic

### Supabase
- Monitor database connection limits
- Upgrade plan if storage exceeds limits

### Rate Limiting
The Nginx config includes rate limiting:
- API: 10 requests/second
- Bursts allowed up to 20

---

## 10. Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] HTTPS enabled on all endpoints
- [ ] CORS configured for specific origins only
- [ ] RLS enabled on Supabase tables
- [ ] `service_role` key only on backend
- [ ] Webhook token verified on Telegram endpoint
- [ ] Rate limiting enabled

---

## Rollback Procedures

### Vercel
```bash
# List deployments
vercel ls

# Rollback to previous deployment
vercel rollback [deployment-url]
```

### Render
1. Go to Service Dashboard > Events
2. Find previous successful deploy
3. Click **Rollback** button

### Database
- Use Supabase point-in-time recovery (Pro plan)
- Or restore from manual backup

---

*Last updated: January 2026*
