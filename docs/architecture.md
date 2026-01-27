
# System Architecture - MatruRaksha

## Overview
MatruRaksha uses a **Microservices-inspired Monolithic** architecture designed for scalability, resilience, and AI integration.

## 🏗️ High-Level Architecture

```mermaid
graph TD
    User[User (Web/Mobile)] -->|HTTPS| CDN[CDN / Load Balancer]
    CDN -->|Next.js/React| Frontend[Frontend App]
    
    subgraph "Backend Infrastructure (Dockerized)"
        Frontend -->|REST API / SSE| API[FastAPI Backend]
        
        API -->|Auth & Data| Supabase[(Supabase DB & Auth)]
        API -->|Cache & PubSub| Redis[(Redis)]
        
        API -->|Async Tasks| Celery[Celery Worker]
        Celery -->|Queue| Redis
        
        API -->|Metrics| Prometheus[Prometheus]
    end
    
    subgraph "AI Services"
        API -->|Health Insights| Gemini[Google Gemini AI]
        API -->|Voice Interaction| Vapi[Vapi.ai Voice Agent]
        
        Celery -->|Batch Analysis| Gemini
    end
    
    subgraph "External Integrations"
        Vapi -->|Telephony| Phone[Mothers' Phones]
        API -->|Notifications| MSG[SMS / Telegram]
    end
```

## 🔌 Core Components

### 1. Backend API (FastAPI)
- **Role**: Central orchestrator.
- **Key Modules**:
  - `routes/auth`: Authentication & RBAC.
  - `routes/santanraksha`: Child health & vaccination.
  - `routes/ai_routes`: AI predictions & insights.
  - `services/cache_service`: Hybrid caching (Redis + In-Memory).

### 2. Database (Supabase / PostgreSQL)
- **Role**: Primary data store.
- **Key Tables**:
  - `mothers`, `children`: Core entities.
  - `risk_assessments`: Medical history.
  - `patient_insights`: AI-generated inferences.

### 3. Asynchronous Processing (Celery + Redis)
- **Role**: Handling heavy workloads off the main thread.
- **Tasks**:
  - PDF Generation (`EportService`).
  - Periodic AI Health Scans.
  - Sending Bulk Notifications.

### 4. AI & Intelligence
- **Predictive Engine**: `AIPredictionService` (Hybrid Rules + GenAI).
- **Voice Agent**: Vapi.ai integration for automated check-up calls.

## 🛡️ Security
- **Authentication**: JWT via Supabase Auth.
- **Authorization**: Role-Based Access Control (Admin, Doctor, ASHA).
- **Audit**: `audit_logs` table tracks all critical modifications.
- **Network**: All internal traffic on private Docker network.

## 📊 Observability
- **Logs**: JSON structured logs (Production).
- **Metrics**: Prometheus (`/metrics`) for latency and error rates.
- **Health**: Deep health checks at `/health/ready`.
