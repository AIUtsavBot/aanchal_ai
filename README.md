
# 🏥 Aanchal AI

> **"Protecting Mothers, Nurturing Future"**

**Aanchal AI** is a comprehensive digital health ecosystem designed to combat maternal and infant mortality. It serves as the umbrella platform for two specialized AI-driven products:

1.  **MatruRaksha AI** 🤰 - Dedicated to **Maternal Health** (Pregnancy to Postpartum).
2.  **SantanRaksha AI** 👶 - Dedicated to **Child Health** (Neonatal to Infant care).

By leveraging Artificial Intelligence, real-time data analytics, and a resilient microservices architecture, Aanchal AI bridges the gap between rural healthcare workers (ASHAs) and medical specialists.

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-purple)
![Tech](https://img.shields.io/badge/Stack-FastAPI%20|%20React%20|%20Supabase-orange)

## 🌟 Solution Overview

In many regions, health data is fragmented and reactive. Aanchal AI transforms this into a **proactive, compassionate system**:

### 🤰 MatruRaksha AI (Maternal Focus)
*   **For Mothers**: Personalized care plans, emergency alerts, and tracking of vital stats during pregnancy.
*   **For ASHAs**: Offline-first data entry for prenatal checkups (ANC) and risk identification.
*   **AI Engine**: Predicts risks like Preeclampsia utilizing clinical rules + ML trends.

### 👶 SantanRaksha AI (Child Focus)
*   **For Neonates**: Monitoring growth charts, vaccination schedules, and developmental milestones.
*   **For Doctors**: AI-generated summaries of a child's health history to enable quick decision-making.

---

## 🚀 Key Capabilities

### 🧠 Phase 5: AI Health Intelligence
-   **Predictive Risk Engine**: Hybrid model for flagging high-risk cases.
-   **GenAI Summaries**: Google Gemini generates concise clinical notes for doctors.
-   **Voice Agent**: Vapi.ai integration for automated follow-up calls in local languages.

### 🌐 Phase 6: Omni-Channel Access
-   **Offline PWA**: Field-ready mobile experience that caches data and syncs when online.
-   **Push Notifications**: Browser-based alerts for emergencies and upcoming visits.

### 🛡️ Phase 4: Security & Observability
-   **Audit Trails**: Immutable logs of all data access and modifications (`audit_logs`).
-   **Deep Health Checks**: Real-time monitoring of Database, Cache, and AI APIs.
-   **Resilience**: Global Error Boundaries, API Retry logic.

---

## 🏗️ System Architecture

Aanchal AI acts as the central brain, orchestrating data flow between users and intelligent services.

```mermaid
graph TD
    subgraph "Users & Touchpoints"
        Mother[Mother / Family]
        ASHA[ASHA Worker (Field)]
        Doctor[Doctor (Hospital)]
        Admin[Administrator]
    end

    subgraph "Frontend Layer (PWA)"
        WebPC[Web Portal]
        Mobile[Mobile PWA (Offline)]
    end

    subgraph "Aanchal AI Core Platform"
        API[FastAPI Gateway]
        Auth[Auth Service]
        
        subgraph "Products"
            MR[MatruRaksha AI Service]
            SR[SantanRaksha AI Service]
        end
        
        Orch[Task Orchestrator (Celery)]
    end

    subgraph "Data & Knowledge"
        DB[(Supabase PostgreSQL)]
        Cache[(Redis Cache)]
        Vector[Vector DB (Medical Context)]
    end

    subgraph "External AI Services"
        Gemini[Google Gemini 2.0 (Reasoning)]
        Vapi[Vapi.ai (Voice Agents)]
        SMS[Twilio / SMS Gateway]
    end

    %% Flows
    Mother -->|SMS / Voice| Vapi
    ASHA -->|Offline Entry| Mobile
    Doctor -->|Dashboard| WebPC
    Admin -->|Analytics| WebPC

    Mobile -->|Sync| API
    WebPC -->|HTTPS| API

    API --> Auth
    API --> MR
    API --> SR
    
    MR --> Orch
    SR --> Orch
    
    Orch -->|Risk Analysis| Gemini
    Orch -->|Alerts| SMS
    Orch -->|Schedule Call| Vapi
    
    API --> DB
    API --> Cache
    Gemini -.->|RAG| Vector
```

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Core AI** | **Aanchal AI Engine** | Central logic for risk assessment |
| **Backend** | Python 3.12, FastAPI | High-performance async API |
| **Frontend** | React 18, Vite, Tailwind | Responsive PWA with offline support |
| **Database** | Supabase (PostgreSQL) | Relational data + Vector embeddings |
| **AI Services** | Google Gemini 2.0, Vapi.ai | LLM & Voice capabilities |

---

## ⚡ Quick Start Guide

### 1. Requirements
-   Docker & Docker Compose
-   *Or* Python 3.12+ & Node.js 18+ for local dev.

### 2. Environment Setup
Create a `.env` file in `backend/` and `frontend/` (see `.env.example`).
Required keys: `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`.

### 3. Run with Docker (Recommended)
Launch the entire Aanchal AI stack:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```
-   **Frontend**: http://localhost
-   **Backend API**: http://localhost:8000/docs

### 4. Seed Demo Data
Populate the system with realistic patients:
```bash
python scripts/seed_demo_data.py
```

### 5. Run Tests
```bash
pytest backend/tests/
```

---

## 📚 Documentation Links
-   [**Detailed Architecture**](docs/architecture.md)
-   [**Deployment Guide**](docs/deployment.md)
-   [**Walkthrough**](walkthrough.md)
-   [**Contributor Guide**](CONTRIBUTING.md)

---

## 🤝 Contact & License

**Antigravity Team**
*Google Deepmind Agentic Coding*
License: MIT
