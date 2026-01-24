# MatruRaksha AI - System Architecture

> Comprehensive system design documentation for the Maternal Health Monitoring Platform

---

## System Overview

MatruRaksha AI is an AI-powered maternal health monitoring system designed for low-resource settings in India. It provides 24/7 health monitoring, risk assessment, and emergency response capabilities through multiple channels.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MatruRaksha AI System                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │   Telegram   │    │  Web Portal  │    │  Mobile App  │                 │
│   │     Bot      │    │   (React)    │    │(React Native)│                 │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                              │
│                    ┌─────────▼─────────┐                                    │
│                    │   FastAPI Backend │                                    │
│                    │   (Python 3.12)   │                                    │
│                    └─────────┬─────────┘                                    │
│                              │                                              │
│         ┌────────────────────┼────────────────────┐                         │
│         │                    │                    │                         │
│   ┌─────▼─────┐       ┌──────▼─────┐      ┌──────▼──────┐                  │
│   │ AI Agents │       │  Supabase  │      │   Gemini    │                  │
│   │ Orchestra │       │  Database  │      │     AI      │                  │
│   └───────────┘       └────────────┘      └─────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Components

### 1. Frontend Layer

#### Web Portal (React + Vite)
- **Technology**: React 18, Vite, TailwindCSS
- **Features**:
  - Role-based dashboards (Admin, Doctor, ASHA Worker)
  - Real-time updates via Supabase subscriptions
  - Multi-language support (English, Hindi, Marathi)
  - Medical report upload and viewing
  - Risk assessment visualization

#### Telegram Bot
- **Technology**: python-telegram-bot v21+
- **Features**:
  - Mother registration and profile management
  - Document upload for AI analysis
  - Health check-ins
  - Emergency alerts
  - Multi-profile support (same chat, multiple mothers)

#### Mobile App (React Native)
- **Technology**: React Native with Expo
- **Features**: Offline-first architecture, sync capabilities

---

### 2. Backend Layer (FastAPI)

```
backend/
├── main.py                 # Application entry point
├── enhanced_api.py         # Extended API endpoints
├── telegram_bot.py         # Telegram bot logic
├── scheduler.py            # Cron jobs and scheduled tasks
├── routes/
│   ├── auth_routes.py      # Authentication endpoints
│   ├── admin_routes.py     # Admin management endpoints
│   └── vapi_routes.py      # Voice AI calling endpoints
├── agents/
│   ├── orchestrator.py     # AI agent coordination
│   ├── risk_agent.py       # Risk assessment
│   ├── nutrition_agent.py  # Nutritional guidance
│   ├── medication_agent.py # Medication reminders
│   ├── care_agent.py       # Care recommendations
│   └── emergency_agent.py  # Emergency handling
├── services/
│   ├── auth_service.py     # Authentication logic
│   ├── supabase_service.py # Database operations
│   ├── telegram_service.py # Telegram messaging
│   ├── cache_service.py    # In-memory caching
│   └── email_service.py    # Email notifications
└── middleware/
    └── auth.py             # JWT authentication
```

---

### 3. AI Agent Orchestra

The system uses a multi-agent architecture for comprehensive maternal health support:

```
                     ┌──────────────────┐
                     │   Orchestrator   │
                     │  (Agent Router)  │
                     └────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │           │         │         │           │
   ┌────▼───┐  ┌────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌────▼────┐
   │  Risk  │  │Nutrition│ │Medication│ │ Care │ │Emergency│
   │ Agent  │  │ Agent   │ │  Agent  │ │Agent │ │  Agent  │
   └────────┘  └─────────┘ └─────────┘ └──────┘ └─────────┘
```

#### Agent Descriptions:

| Agent | Purpose | Triggers |
|-------|---------|----------|
| **Risk Agent** | Analyzes health data to calculate risk scores | Vitals submission, report upload |
| **Nutrition Agent** | Provides dietary recommendations | User queries, pregnancy stage changes |
| **Medication Agent** | Manages medication schedules and reminders | Daily check-ins, appointment creation |
| **Care Agent** | Offers general maternal care guidance | User questions, health concerns |
| **Emergency Agent** | Handles high-risk alerts and escalation | Risk score > 0.7, symptom detection |

---

### 4. Database Layer (Supabase)

#### Core Tables

```sql
-- Mother profiles
mothers (id, name, phone, age, gravida, parity, bmi, location, 
         preferred_language, telegram_chat_id, due_date, 
         medical_history, asha_worker_id, doctor_id)

-- Healthcare providers
doctors (id, name, phone, assigned_area, email, user_profile_id)
asha_workers (id, name, phone, assigned_area, email, user_profile_id)

-- Health tracking
health_timeline (id, mother_id, event_date, event_type, blood_pressure,
                 hemoglobin, sugar_level, weight, concerns, summary)
                 
medical_reports (id, mother_id, filename, file_url, analysis_status,
                 analysis_result, extracted_metrics)

-- User authentication
user_profiles (id, email, full_name, phone, role, is_active, 
               assigned_area, avatar_url)
               
registration_requests (id, email, full_name, role_requested, status,
                       degree_cert_url, reviewed_by, review_note)
```

#### Row Level Security (RLS)
- Users can only access their own profile
- Admins have full access
- Doctors can view ASHA workers in their area
- ASHA workers can view assigned mothers

---

### 5. External Integrations

```
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐    │
│  │ Gemini  │  │Telegram │  │ Resend  │  │   Vapi AI   │    │
│  │   AI    │  │   API   │  │  Email  │  │ Voice Calls │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘    │
│                                                              │
│  • Document   • Bot        • Alerts     • Automated         │
│    Analysis     Messages   • Notifs       Check-ins         │
│  • Chat AI    • Webhooks   • Reports    • Voice AI          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Mother Registration Flow

```
User → Telegram /start → Show Dashboard
                       ↓
              [Register Button]
                       ↓
         Collect: Name, Age, Phone, Due Date,
                  Location, Gravida, Parity, BMI
                       ↓
              [Confirm Registration]
                       ↓
         Insert into Supabase → Link Telegram Chat ID
                       ↓
         ← Show Home Dashboard with Actions
```

### 2. Document Analysis Flow

```
Mother/ASHA → Upload Document (PDF/Image)
                       ↓
         Store in Supabase Storage
                       ↓
         Trigger Gemini AI Analysis
                       ↓
         Extract: Hemoglobin, BP, Blood Sugar, etc.
                       ↓
         Calculate Risk Score
                       ↓
         If High Risk → Send Alert to Telegram
                       ↓
         Store Analysis Results in Database
```

### 3. Emergency Alert Flow

```
High Risk Detected (Score > 0.7)
                       ↓
         Emergency Agent Activated
                       ↓
         ├→ Telegram: Alert Mother
         ├→ Telegram: Alert ASHA Worker
         ├→ Email: Notify Assigned Doctor
         └→ SMS: If configured (Fast2SMS)
```

---

## Security Architecture

### Authentication Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   Authentication Flow                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐     ┌──────────────┐     ┌─────────────────┐   │
│  │  User   │────▶│ Supabase Auth│────▶│ JWT Access Token│   │
│  └─────────┘     └──────────────┘     └─────────────────┘   │
│       │                                        │              │
│       │          ┌──────────────┐              │              │
│       └─────────▶│ Google OAuth │──────────────┘              │
│                  └──────────────┘                             │
│                                                               │
│  Role Assignment: ADMIN → Full Access                         │
│                   DOCTOR → Patient Data + Assignments         │
│                   ASHA_WORKER → Assigned Mothers Only         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Role-Based Access Control (RBAC)

| Role | Capabilities |
|------|--------------|
| **ADMIN** | Full system access, user management, all data |
| **DOCTOR** | View assigned patients, case discussions, reports |
| **ASHA_WORKER** | Register mothers, upload reports, daily check-ins |
| **MOTHER** (Telegram) | View own data, check-ins, document uploads |

---

## Deployment Architecture

### Development
```
Frontend: localhost:5173 (Vite dev server)
Backend:  localhost:8000 (Uvicorn)
Database: Supabase Cloud
```

### Production
```
Frontend: Vercel (matru-raksha-ai-event.vercel.app)
Backend:  Render (matruraksha-ai-event.onrender.com)
Database: Supabase (Postgres + Storage)
Telegram: Webhook mode for efficiency
```

### Docker Deployment
```
docker-compose up -d

Services:
├── frontend  (Nginx + React build)
├── backend   (Gunicorn + FastAPI)
└── redis     (Optional caching)
```

---

## Scalability Considerations

1. **Caching Layer**: In-memory cache service with TTL for dashboard stats
2. **Database**: Supabase provides automatic scaling
3. **Telegram**: Webhook mode (no polling overhead)
4. **AI Calls**: Rate limiting to manage Gemini API costs
5. **Background Tasks**: FastAPI BackgroundTasks for async processing

---

## Monitoring & Logging

- **Structured Logging**: JSON format with timestamps
- **Health Endpoint**: `/health` for load balancer checks
- **Error Tracking**: Comprehensive exception logging
- **Emoji Indicators**: Visual status in logs (✅ ❌ ⚠️ 🤖)

---

*Last updated: January 2026*
