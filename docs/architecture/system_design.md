# 🏗️ MatruRaksha System Design

> Comprehensive architectural overview of the MatruRaksha AI maternal health monitoring system.

---

## 📋 Table of Contents

- [System Overview](#-system-overview)
- [High-Level Architecture](#-high-level-architecture)
- [Component Details](#-component-details)
- [Data Flow](#-data-flow)
- [AI Agent Architecture](#-ai-agent-architecture)
- [Security Architecture](#-security-architecture)
- [Scalability Considerations](#-scalability-considerations)
- [Technology Decisions](#-technology-decisions)

---

## 🔍 System Overview

MatruRaksha AI is a comprehensive maternal health monitoring system designed for underserved communities in India. The system leverages AI agents, real-time communication, and healthcare worker coordination to provide 24/7 support for pregnant mothers.

### Design Principles

1. **Accessibility First** - Works via Telegram for low-bandwidth environments
2. **AI-Powered Insights** - Gemini AI for intelligent health analysis
3. **Real-time Alerts** - Immediate emergency detection and notification
4. **Role-Based Access** - Secure access for Doctors, ASHA workers, and Admins
5. **Performance Optimized** - In-memory caching for fast dashboard loads

---

## 🏛️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  🤰 Mothers          👩‍⚕️ ASHA Workers      👨‍⚕️ Doctors         👨‍💼 Admins        │
│  (Telegram/Web)      (Web Dashboard)      (Web Dashboard)     (Admin Portal) │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│   📱 Telegram API    │  │   🌐 React SPA   │  │   📧 Email Service   │
│   (Bot Gateway)      │  │   (Vite + React) │  │   (Resend API)       │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                        ⚡ FastAPI Backend (:8000)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ Auth Routes │  │ Admin Routes│  │ Risk Routes │  │ Analytics Routes│     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    🔒 JWT Authentication Middleware                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│   🤖 AI Agents       │  │  📦 Cache Service │  │   📊 Services        │
│   (Gemini Powered)   │  │  (In-Memory TTL)  │  │   (Business Logic)   │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐      │
│  │ 🗄️ PostgreSQL   │  │ 🔐 Supabase Auth │  │ 📁 Supabase Storage    │      │
│  │ (Supabase)      │  │ (JWT + OAuth)    │  │ (Documents/Certs)      │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Details

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── pages/                    # Route-level components
│   │   ├── Home.jsx              # Landing page
│   │   ├── RiskDashboard.jsx     # Risk monitoring dashboard
│   │   ├── DoctorDashboard.jsx   # Doctor patient management
│   │   ├── ASHAInterface.jsx     # ASHA worker interface
│   │   ├── AdminDashboard.jsx    # Admin management portal
│   │   └── AdminApprovals.jsx    # User approval center
│   │
│   ├── components/               # Reusable UI components
│   │   ├── Navbar.jsx            # Navigation header
│   │   ├── PatientCard.jsx       # Patient summary card
│   │   ├── RiskChart.jsx         # Risk visualization
│   │   ├── CaseChat.jsx          # Real-time case discussions
│   │   └── ProtectedRoute.jsx    # Route authorization
│   │
│   ├── contexts/                 # React Context providers
│   │   └── AuthContext.jsx       # Authentication state management
│   │
│   └── services/                 # API integration
│       ├── api.js                # Axios HTTP client
│       └── auth.js               # Supabase Auth wrapper
```

**Key Design Decisions:**
- **Vite** for fast HMR and optimized builds
- **Tailwind CSS** for rapid UI development
- **React Context** for auth state (no Redux needed)
- **Supabase Realtime** for live updates in CaseChat

---

### Backend (FastAPI)

```
backend/
├── main.py                       # Application entry point
├── routes/
│   ├── auth_routes.py            # Authentication endpoints
│   ├── admin_routes.py           # Admin CRUD operations
│   └── vapi_routes.py            # Voice AI endpoints
│
├── services/
│   ├── auth_service.py           # User authentication logic
│   ├── cache_service.py          # In-memory TTL caching
│   ├── email_service.py          # Resend email integration
│   ├── sms_service.py            # Fast2SMS integration
│   ├── supabase_service.py       # Database operations
│   └── telegram_service.py       # Telegram bot logic
│
├── agents/                       # AI Agent system
│   ├── orchestrator.py           # Agent coordination
│   ├── base_agent.py             # Abstract agent class
│   ├── risk_agent.py             # Risk assessment
│   ├── emergency_agent.py        # Emergency detection
│   ├── nutrition_agent.py        # Nutrition advice
│   ├── medication_agent.py       # Medication management
│   ├── care_agent.py             # Care planning
│   └── asha_agent.py             # ASHA coordination
│
├── middleware/
│   └── auth.py                   # JWT verification middleware
│
└── models/
    ├── database.py               # Supabase client setup
    └── schemas.py                # Pydantic models
```

**Key Design Decisions:**
- **FastAPI** for async support and automatic OpenAPI docs
- **Pydantic** for request/response validation
- **Service Layer Pattern** for business logic separation
- **In-Memory Cache** (no Redis dependency for simplicity)

---

### AI Agent System

```
┌────────────────────────────────────────────────────────────────────┐
│                      🎯 ORCHESTRATOR                                │
│   - Intent Classification (Gemini AI)                               │
│   - Context Building                                                │
│   - Agent Selection & Routing                                       │
│   - Response Aggregation                                            │
└────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ ⚠️ Risk      │      │ 🚨 Emergency │      │ 🥗 Nutrition │
│ Assessment   │      │ Detection    │      │ Planning     │
│ Agent        │      │ Agent        │      │ Agent        │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ • BP Analysis│      │ • Danger Sign│      │ • Meal Plans │
│ • Risk Score │      │ • Alert Gen  │      │ • Supplements│
│ • Trending   │      │ • Escalation │      │ • Diet Tips  │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ 💊 Medication│      │ 💚 Care      │      │ 👩‍⚕️ ASHA     │
│ Management   │      │ Planning     │      │ Coordination │
│ Agent        │      │ Agent        │      │ Agent        │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ • Reminders  │      │ • Daily Tasks│      │ • Visit Plan │
│ • Interaction│      │ • Exercise   │      │ • Checklists │
│ • Compliance │      │ • Checkups   │      │ • Follow-ups │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## 🔄 Data Flow

### Risk Assessment Flow

```
User Input → API Gateway → Auth Middleware → Risk Agent
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                            Gemini Analysis              Rule Engine
                            (AI Risk Factors)        (BP, Hb Thresholds)
                                    │                           │
                                    └─────────────┬─────────────┘
                                                  ▼
                                         Combined Risk Score
                                                  │
                              ┌───────────────────┼───────────────────┐
                              ▼                   ▼                   ▼
                        LOW Risk            MODERATE Risk        HIGH Risk
                        (Score 0-30)        (Score 31-70)       (Score 71-100)
                              │                   │                   │
                              ▼                   ▼                   ▼
                        Save to DB          Save + Notify       Emergency Alert
                                            ASHA Worker          + All Staff
```

### Authentication Flow

```
┌─────────┐   OAuth    ┌────────────┐  Redirect   ┌─────────────┐
│  User   │──────────▶ │  Supabase  │───────────▶ │  Frontend   │
└─────────┘            │   Auth     │             │  Callback   │
                       └────────────┘             └──────┬──────┘
                                                         │
                              ┌───────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────┐
│               ROLE SELECTION                         │
│   ┌─────────────┐            ┌─────────────────┐    │
│   │   DOCTOR    │            │   ASHA WORKER   │    │
│   │ (Upload Cert)│           │                  │    │
│   └─────────────┘            └─────────────────┘    │
└─────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌─────────────────────┐
                  │  Registration       │
                  │  Request (PENDING)  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Admin Reviews      │
                  │  & Approves         │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Role Assigned      │
                  │  Access Granted     │
                  └─────────────────────┘
```

---

## 🔐 Security Architecture

### Authentication Layers

1. **Supabase Auth** - OAuth 2.0 + JWT tokens
2. **Row Level Security (RLS)** - Database-level access control
3. **Backend Middleware** - JWT verification on all protected routes
4. **Role-Based Access Control (RBAC)** - ADMIN, DOCTOR, ASHA_WORKER roles

### Security Measures

| Layer | Measure | Implementation |
|-------|---------|----------------|
| Transport | HTTPS | SSL/TLS on all endpoints |
| Auth | JWT | Supabase issues, backend verifies |
| Database | RLS | Supabase policies per table |
| API | Rate Limiting | FastAPI middleware |
| Secrets | Encryption | Environment variables, never in code |
| Uploads | Validation | File type and size checks |

---

## 📈 Scalability Considerations

### Current Architecture (MVP)

- **Single Backend Instance** - Suitable for 1000s of users
- **In-Memory Cache** - 30s TTL, reduces DB load by 70%
- **Supabase** - Managed PostgreSQL with auto-scaling

### Future Scaling Path

```
Current                          Scale-Up                          Scale-Out
   │                                 │                                  │
   ▼                                 ▼                                  ▼
┌──────────┐                  ┌──────────────┐                  ┌──────────────┐
│ 1 Server │    ──────▶       │ Larger VM    │    ──────▶       │ K8s Cluster  │
│ In-Memory│    Vertical      │ Add Redis    │    Horizontal    │ Load Balancer│
│ Cache    │                  │ Connection   │                  │ Redis Cluster│
│          │                  │ Pooling      │                  │ Read Replicas│
└──────────┘                  └──────────────┘                  └──────────────┘
   │                                 │                                  │
   ├── 1K users                      ├── 10K users                      ├── 100K+ users
   ├── $20/mo                        ├── $100/mo                        ├── $500+/mo
   └── MVP Phase                     └── Growth Phase                   └── Scale Phase
```

---

## 🛠️ Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Backend Framework** | FastAPI | Async, auto-docs, type hints |
| **Database** | Supabase (PostgreSQL) | Managed, RLS, Realtime, Storage |
| **Frontend** | React + Vite | Fast dev experience, large ecosystem |
| **Styling** | Tailwind CSS | Rapid prototyping, consistent design |
| **AI Model** | Gemini 2.5 Flash | Low latency, cost-effective, Indian language support |
| **Messaging** | Telegram Bot API | Wide reach, works on 2G, no app install |
| **Email** | Resend | Simple API, good deliverability |
| **SMS** | Fast2SMS | Free tier for India, reliable |
| **Caching** | In-Memory (TTL) | Zero infrastructure, sufficient for MVP |
| **Auth** | Supabase Auth | Google OAuth, JWT, built-in |

---

## 📚 Related Documentation

- [Database Schema](./database_schema.md)
- [API Endpoints](../api/endpoints.md)
- [Deployment Guide](../guides/deployment_guide.md)
- [Setup Guide](../guides/setup_guide.md)

---

*Last Updated: January 2026*
