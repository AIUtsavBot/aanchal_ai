
# 🤰 MatruRaksha AI - Maternal & Child Health Platform

> **"Protecting Mothers, Nurturing Future"**

**MatruRaksha AI** is an enterprise-grade digital health platform built to combat maternal and infant mortality. By leveraging Artificial Intelligence, real-time data analytics, and a resilient microservices architecture, it bridges the gap between rural healthcare workers (ASHAs) and medical specialists.

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-purple)
![Tech](https://img.shields.io/badge/Stack-FastAPI%20|%20React%20|%20Supabase-orange)

## 🌟 Solution Overview

In many regions, maternal health data is fragmented, paper-based, and reactive. MatruRaksha transforms this into a **proactive, data-driven system**:

1.  **For ASHA Workers**: A Progressive Web App (PWA) that works **offline**, allowing them to record vitals and vaccinations in remote villages.
2.  **For Doctors**: An AI-powered dashboard that **auto-triage** high-risk cases and provides generated clinical summaries.
3.  **For Administrators**: Real-time analytics on vaccination coverage, disease outbreaks, and worker performance.

---

## 🚀 Key Capabilities

### 🧠 Phase 5: AI Health Intelligence
- **Predictive Risk Engine**: Uses a hybrid model (Clinical Rules + ML Trends) to flag high-risk mothers (e.g., Preeclampsia risk).
- **GenAI Summaries**: Google Gemini generates concise 3-line clinical summaries for busy doctors.
- **Voice Agent**: Vapi.ai integration for automated follow-up calls in local languages.

### � Phase 6: Omni-Channel Access
- **Offline PWA**: Field-ready mobile experience that caches data and syncs when online.
- **Push Notifications**: Browser-based alerts for emergencies and upcoming visits.

### 🛡️ Phase 4: Security & Observability
- **Audit Trails**: Immutable logs of all data access and modifications (`audit_logs`).
- **Deep Health Checks**: Real-time monitoring of Database, Cache, and AI APIs (`/health/ready`).
- **Resilience**: Global Error Boundaries, API Retry logic, and formatting for "System Down" scenarios.

### ⚡ Phase 2: High Performance
- **Hybrid Caching**: Redis + In-Memory caching for <200ms API response times.
- **Async Workers**: Celery/Redis for handling PDF generation and heavy AI tasks without blocking.

---

## 🏗️ System Architecture

MatruRaksha follows a modular architecture designed for scalability.

```mermaid
graph TD
    Client[User (PWA/Mobile)] -->|HTTPS| CDN[CDN / Load Balancer]
    CDN -->|React| Frontend[Frontend PWA]
    
    subgraph "Backend Infrastructure"
        Frontend -->|REST / SSE| API[FastAPI Backend]
        API -->|Auth & Data| DB[(Supabase Postgres)]
        API -->|Cache| Redis[(Redis)]
        API -->|Async Tasks| Worker[Celery Worker]
    end
    
    subgraph "Intelligence Layer"
        API -->|Inference| Gemini[Google Gemini AI]
        API -->|Voice| Vapi[Vapi.ai]
    end
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | Python 3.12, FastAPI | High-performance async API |
| **Frontend** | React 18, Vite, Tailwind | Responsive PWA with offline support |
| **Database** | Supabase (PostgreSQL) | Relational data + Vector embeddings |
| **Caching** | Redis (Upstash) | Distributed caching & Pub/Sub |
| **Queue** | Celery | Background task processing |
| **AI** | Google Gemini 2.0 | LLM for summarization & reasoning |
| **DevOps** | Docker, GitHub Actions | CI/CD and Containerization |

---

## ⚡ Quick Start Guide

### 1. Requirements
- Docker & Docker Compose
- *Or* Python 3.12+ & Node.js 18+ for local dev.

### 2. Environment Setup
Create a `.env` file in `backend/` and `frontend/` (see `.env.example`).
Required keys: `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`.

### 3. Run with Docker (Recommended)
Launch the entire stack (Backend, Frontend, Redis, Workers) with one command:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000/docs

### 4. Seed Demo Data
Populate the system with realistic patients to see the AI in action:
```bash
python scripts/seed_demo_data.py
```

### 5. Run Tests
Verify system integrity:
```bash
# Backend Tests
pytest backend/tests/

# Load Testing
locust -f locustfile.py
```

---

## 📚 Documentation Links

- [**Detailed Architecture**](docs/architecture.md): Deep dive into the system design.
- [**Deployment Guide**](docs/deployment.md): Instructions for Vercel/Render/AWS.
- [**Walkthrough**](walkthrough.md): Feature-by-feature proof of work.
- [**Contributor Guide**](CONTRIBUTING.md): Standards for developers.

---

## 🔮 Future Roadmap

- [ ] **Mobile App**: Dedicated React Native app for smoother animations.
- [ ] **Biometric Auth**: Fingerprint login for ASHA workers.
- [ ] **Telemedicine**: Integrated video calls between Mothers and Doctors.
- [ ] **Vernacular Voice**: Full conversational AI in Hindi/Tamil/Telugu.

---

## 🤝 Contact & License

**Antigravity Team**  
*Google Deepmind Agentic Coding*  
icense: MIT
