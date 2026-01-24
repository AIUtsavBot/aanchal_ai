# 🤰 MatruRaksha AI + 🍼 SantanRaksha

> **Complete Maternal & Child Health Care System** - From Pregnancy to Postnatal Recovery & Child Development

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-orange.svg)](https://supabase.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-purple.svg)](https://ai.google.dev/)

---

## 🎯 Overview

This system provides **end-to-end maternal and child health care** through two integrated modules:

| Module | Focus | Features |
|--------|-------|----------|
| **🤰 MatruRaksha** | Pregnancy Care | Risk assessment, symptom tracking, AI health guidance |
| **🍼 SantanRaksha** | Postnatal & Child Care | Vaccination tracking, growth monitoring, milestone tracking |

### Target Users

| User | Access | Features |
|------|--------|----------|
| 🤰 **Mother** | Telegram Bot, Web | Health queries, check-ins, emergency alerts |
| 👩‍⚕️ **ASHA Worker** | Web Dashboard | Patient monitoring, visits, assessments, toggle between pregnancy/postnatal |
| 👨‍⚕️ **Doctor** | Web Dashboard | Case review, risk assessments, consultations, toggle between pregnancy/postnatal |
| 👨‍💼 **Admin** | Web Dashboard | User management, approvals |

---

## 🏗️ Complete Architecture

### High-Level System Design

```mermaid
flowchart TB
    subgraph USERS[" USERS "]
        Mother["Mother"]
        ASHA["ASHA Worker"]
        Doctor["Doctor"]
        Admin["Admin"]
    end

    subgraph FRONTEND[" FRONTEND - React "]
        WebApp["Web Dashboard :5173"]
        OfflineSync["Offline Sync Service"]
        IndexedDB[("IndexedDB")]
    end

    subgraph TELEGRAM[" TELEGRAM "]
        TGBot["MatruRaksha Bot"]
    end

    subgraph BACKEND[" BACKEND - FastAPI "]
        API["REST API :8000"]
        Orchestrator["AI Orchestrator"]
        RAGService["Hybrid RAG Service"]
        SyncRoutes["Offline Sync Routes"]
    end

    subgraph AI_AGENTS[" AI AGENTS "]
        Risk["Risk Agent"]
        Care["Care Agent"]
        Nutrition["Nutrition Agent"]
        Medication["Medication Agent"]
        Emergency["Emergency Agent"]
        ASHAAgent["ASHA Agent"]
        Postnatal["Postnatal Agent"]
        Pediatric["Pediatric Agent"]
        Vaccine["Vaccine Agent"]
        Growth["Growth Agent"]
    end

    subgraph EXTERNAL[" EXTERNAL SERVICES "]
        Gemini["Gemini AI"]
        GeminiEmbed["Gemini Embeddings"]
        Resend["Resend Email"]
    end

    subgraph DATABASE[" SUPABASE "]
        PG[("PostgreSQL")]
        pgvector[("pgvector")]
        Auth["Supabase Auth"]
        Storage[("File Storage")]
    end

    Mother --> TGBot
    Mother --> WebApp
    ASHA --> WebApp
    Doctor --> WebApp
    Admin --> WebApp

    TGBot --> API
    WebApp --> OfflineSync
    OfflineSync <--> IndexedDB
    OfflineSync --> API

    API --> Orchestrator
    API --> RAGService
    API --> SyncRoutes
    
    Orchestrator --> Risk
    Orchestrator --> Care
    Orchestrator --> Nutrition
    Orchestrator --> Medication
    Orchestrator --> Emergency
    Orchestrator --> ASHAAgent
    Orchestrator --> Postnatal
    Orchestrator --> Pediatric
    Orchestrator --> Vaccine
    Orchestrator --> Growth
    
    RAGService --> GeminiEmbed
    RAGService --> pgvector
    
    Risk --> Gemini
    Care --> Gemini
    
    API --> PG
    API --> Auth
    API --> Storage
    API --> Resend
```

### AI Agent Orchestrator Flow

```mermaid
flowchart LR
    Query["User Query"] --> Classify{"Classify Intent"}
    
    Classify -->|"Pregnancy Risk"| Risk["RiskAgent"]
    Classify -->|"General Care"| Care["CareAgent"]
    Classify -->|"Diet/Nutrition"| Nutrition["NutritionAgent"]
    Classify -->|"Medications"| Medication["MedicationAgent"]
    Classify -->|"Emergency"| Emergency["EmergencyAgent"]
    Classify -->|"ASHA Support"| ASHA["ASHAAgent"]
    Classify -->|"Postnatal Recovery"| Postnatal["PostnatalAgent"]
    Classify -->|"Child Illness"| Pediatric["PediatricAgent"]
    Classify -->|"Vaccination"| Vaccine["VaccineAgent"]
    Classify -->|"Growth/Nutrition"| Growth["GrowthAgent"]
    
    Risk --> RAG["RAG Context"]
    Care --> RAG
    Nutrition --> RAG
    Medication --> RAG
    Emergency --> RAG
    ASHA --> RAG
    Postnatal --> RAG
    Pediatric --> RAG
    Vaccine --> RAG
    Growth --> RAG
    
    RAG --> Gemini["Gemini 2.5 Flash"]
    Gemini --> Response["AI Response"]
```

### Hybrid RAG System

Retrieval-Augmented Generation using 1,015 maternal health cases for context-aware AI responses.

```mermaid
flowchart TB
    Query["User Query: 28yr, BP 140/90, BS 15"]
    
    subgraph FILTER["STEP 1: Metadata Filtering"]
        F1["Filter by age range 25-35"]
        F2["Filter by risk level"]
        F3["Filter by BP ranges"]
    end
    
    subgraph RETRIEVAL["STEP 2: Hybrid Retrieval"]
        BM25["BM25 Sparse Search"]
        PGVEC["pgvector Dense Search"]
    end
    
    subgraph FUSION["STEP 3: Reciprocal Rank Fusion"]
        RRF["Combine BM25 + pgvector scores"]
        TOPK["Top-K similar cases"]
    end
    
    subgraph GEMINI["STEP 4: Gemini AI + Context"]
        CTX["Similar Cases Context"]
        LLM["Gemini 2.5 Flash"]
        RESP["Response with evidence"]
    end
    
    Query --> FILTER
    F1 --> BM25
    F2 --> BM25
    F3 --> BM25
    F1 --> PGVEC
    F2 --> PGVEC
    F3 --> PGVEC
    BM25 --> RRF
    PGVEC --> RRF
    RRF --> TOPK
    TOPK --> CTX
    CTX --> LLM
    LLM --> RESP
```

### Offline-First Data Sync

Ensures forms, chats, and documents are never lost in low-connectivity areas.

```mermaid
flowchart TB
    Action["User Action: Form Submit / Chat / Doc Upload"]
    
    subgraph CHECK["Network Check"]
        Online{"navigator.onLine?"}
    end
    
    subgraph ONLINE_PATH["ONLINE PATH"]
        API["API Call"]
        SB1[("Supabase")]
        Success["Success"]
    end
    
    subgraph OFFLINE_PATH["OFFLINE PATH"]
        IDB[("IndexedDB")]
        PF["pendingForms"]
        PC["pendingChats"]
        PD["pendingDocs"]
        Saved["Saved Locally"]
    end
    
    subgraph SYNC["Auto-Sync on Reconnect"]
        Event["online event"]
        Batch["POST /api/sync/batch"]
        SB2[("Supabase")]
        Clear["Clear IndexedDB"]
        Done["Synced"]
    end
    
    Action --> Online
    Online -->|Yes| API
    API --> SB1
    SB1 --> Success
    
    Online -->|No| IDB
    IDB --> PF
    IDB --> PC
    IDB --> PD
    PF --> Saved
    PC --> Saved
    PD --> Saved
    
    Saved -.-> Event
    Event --> Batch
    Batch --> SB2
    SB2 --> Clear
    Clear --> Done
```

---

## 🔄 User Flows

### Flow 1: Mother Registration and Risk Assessment

```mermaid
sequenceDiagram
    participant M as Mother
    participant T as Telegram Bot
    participant B as Backend API
    participant R as RAG Service
    participant AI as AI Agents
    participant DB as Supabase

    M->>T: /start
    T->>M: Welcome! Lets register you
    M->>T: Provides: Name, Age, Due Date, Location
    T->>B: POST /mothers/register
    B->>DB: Insert mother profile
    B-->>T: Registration success
    T-->>M: Welcome to MatruRaksha!

    Note over M,DB: Daily Health Check-in
    M->>T: My BP is 140/90, feeling dizzy
    T->>B: POST /api/agent/query
    B->>R: get_risk_context age=28, BP=140/90
    R->>R: BM25 search + pgvector search
    R->>R: RRF fusion - Top 5 similar cases
    R-->>B: 3/5 similar cases were HIGH RISK
    B->>AI: Risk Agent + RAG context
    AI-->>B: HIGH RISK - Recommend hospital visit
    B->>DB: Save risk_assessment
    B-->>T: HIGH RISK detected
    T-->>M: Please visit hospital immediately!
```

### Flow 2: ASHA Worker Daily Workflow

```mermaid
sequenceDiagram
    participant A as ASHA Worker
    participant W as Web Dashboard
    participant B as Backend API
    participant AI as AI Agents
    participant DB as Supabase

    A->>W: Login to Dashboard
    W->>B: GET /api/asha/patients
    B->>DB: Query assigned mothers
    DB-->>B: List of 25 mothers
    B-->>W: Patient list with risk levels
    W->>A: Display: 3 HIGH, 5 MID, 17 LOW risk

    Note over A,DB: Home Visit Recording
    A->>W: Select HIGH risk patient
    W->>B: GET /mothers/patient-id
    B-->>W: Full patient history
    A->>W: Record visit: BP reading, symptoms
    W->>B: POST /api/visits
    B->>AI: ASHAAgent analysis
    AI-->>B: Recommendations for next steps
    B->>DB: Save visit record
    B-->>W: Visit saved with AI recommendations
    W->>A: Show recommendations
```

### Flow 3: Delivery to Postnatal Transition

```mermaid
sequenceDiagram
    participant D as Doctor
    participant W as Web Dashboard
    participant B as Backend API
    participant DB as Supabase

    D->>W: Open patient profile
    D->>W: Click Complete Delivery
    W->>B: POST /api/delivery/complete/mother-id
    
    Note over B,DB: System Transition
    B->>DB: Update mother.active_system = santanraksha
    B->>DB: Create child record
    B->>DB: Generate vaccination schedule IAP 2023
    B->>DB: Create postnatal checkup schedule
    DB-->>B: All records created
    B-->>W: Delivery completed successfully

    D->>W: Toggle to Postnatal View
    W->>B: GET /api/children/mother-id
    B-->>W: Child profile + vaccine schedule
    W->>D: Show SantanRaksha Dashboard
```

### Flow 4: Vaccination Tracking

```mermaid
sequenceDiagram
    participant A as ASHA Worker
    participant W as Web Dashboard
    participant B as Backend API
    participant AI as VaccineAgent
    participant DB as Supabase

    A->>W: Open Postnatal View
    A->>W: Select Child
    W->>B: GET /api/vaccinations/child-id
    B->>DB: Query vaccination schedule
    DB-->>B: IAP 2023 schedule with status
    B-->>W: Show due and overdue vaccines

    A->>W: Mark OPV-1 as administered
    W->>B: POST /api/vaccinations/administer
    B->>DB: Update vaccination record
    B-->>W: Success

    Note over A,DB: Parent has concerns
    A->>W: Ask AI about vaccine side effects
    W->>B: POST /api/agent/query
    B->>AI: VaccineAgent query
    AI-->>B: Normal side effects list + when to worry
    B-->>W: AI response
    W->>A: Display guidance for parent
```

---

## 🤖 AI Agents (10 Total)

### MatruRaksha Agents (6)

| Agent | Purpose |
|-------|---------|
| **RiskAgent** | Pregnancy risk assessment |
| **CareAgent** | General prenatal care guidance |
| **NutritionAgent** | Diet and nutrition advice |
| **MedicationAgent** | Safe medication guidance |
| **EmergencyAgent** | Emergency detection and escalation |
| **ASHAAgent** | ASHA worker support |

### SantanRaksha Agents (4)

| Agent | Purpose | Standards |
|-------|---------|-----------|
| **PostnatalAgent** | Mother's recovery (0-6 weeks) | NHM SUMAN, EPDS |
| **PediatricAgent** | Child illness assessment | IMNCI |
| **VaccineAgent** | Immunization guidance | IAP 2023 |
| **GrowthAgent** | Growth & nutrition monitoring | WHO, RBSK |

---

## 📋 Clinical Standards

| Standard | Application |
|----------|-------------|
| **IAP 2023** | 19 vaccines from birth to 2 years |
| **WHO Growth Standards** | Z-score classification for weight/height |
| **RBSK 4Ds** | Developmental screening (Defects, Diseases, Deficiencies, Delays) |
| **NHM SUMAN** | Postnatal care - 6 checkups in 42 days |
| **IMNCI** | Integrated child illness management |
| **WHO IYCF** | Infant feeding recommendations |

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TELEGRAM_BOT_TOKEN=your_bot_token

# Run server
python main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

### 3. Access the App

- **Frontend**: <http://localhost:5173>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

---

## 📁 Project Structure

```
SantanRaksha/
├── README.md                     # This file
├── CHANGELOG.md                  # Version history
├── SANTANRAKSHA.md               # SantanRaksha detailed docs
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py       # Routes to correct agent
│   │   ├── risk_agent.py         # Pregnancy risk
│   │   ├── care_agent.py         # General care
│   │   ├── nutrition_agent.py    # Diet advice
│   │   ├── medication_agent.py   # Safe meds
│   │   ├── emergency_agent.py    # Emergencies
│   │   ├── asha_agent.py         # ASHA support
│   │   ├── postnatal_agent.py    # Postnatal recovery
│   │   ├── pediatric_agent.py    # Child illness
│   │   ├── vaccine_agent.py      # Vaccinations
│   │   └── growth_agent.py       # Growth tracking
│   ├── routes/
│   │   ├── delivery.py           # Delivery completion API
│   │   └── ...
│   ├── services/
│   │   └── rag_service.py        # Hybrid RAG
│   ├── main.py                   # FastAPI app
│   └── telegram_bot.py           # Telegram integration
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # With view toggle
│   │   │   └── ViewToggle.jsx    # Toggle component
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx   # Authentication
│   │   │   └── ViewContext.jsx   # View state (pregnancy/postnatal)
│   │   ├── pages/
│   │   │   ├── ASHAInterface.jsx # ASHA dashboard
│   │   │   ├── DoctorDashboard.jsx # Doctor dashboard
│   │   │   └── postnatal/        # SantanRaksha pages
│   │   │       ├── PostnatalDashboard.jsx
│   │   │       ├── ChildrenList.jsx
│   │   │       ├── VaccinationCalendar.jsx
│   │   │       ├── GrowthCharts.jsx
│   │   │       └── MilestonesTracker.jsx
│   │   └── ...
│   └── ...
│
├── docs/
│   └── API_SPECIFICATION.md      # Full API reference
│
└── infra/
    └── supabase/
        ├── migration_santanraksha_v1.sql  # Children, vaccines, growth tables
        └── migration_delivery_switch.sql  # Delivery completion logic
```

---

## 🔄 User Flow

### Pregnancy → Delivery → Postnatal

```
1. Mother registers via Telegram/Web
       ↓
2. ASHA/Doctor manages in MatruRaksha (Pregnancy View)
       ↓
3. Delivery completed → API call switches to SantanRaksha
       ↓
4. ASHA/Doctor toggles to Postnatal View
       ↓
5. Track vaccinations, growth, milestones
```

### Toggle Usage

1. Login as ASHA Worker or Doctor
2. Go to dashboard (`/asha` or `/doctor`)
3. Find toggle in **blue navigation bar**
4. Click **"🍼 Postnatal"** to switch views
5. Click **"🤰 Pregnancy"** to switch back

---

## 📡 Key API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/signup` | User registration |

### Mothers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mothers/register` | Register new mother |
| GET | `/mothers/{id}` | Get mother details |
| POST | `/api/agent/query` | AI agent query |

### SantanRaksha (New)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/delivery/complete/{mother_id}` | Complete delivery, switch to postnatal |
| GET | `/api/children` | List children |
| POST | `/api/children` | Register child |
| GET | `/api/vaccinations/{child_id}` | Get vaccination schedule |
| POST | `/api/growth/{child_id}` | Add growth record |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI |
| **Frontend** | React 18, Vite |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **AI/LLM** | Google Gemini 2.5 Flash |
| **Auth** | Supabase Auth |
| **Messaging** | Telegram Bot API |
| **Email** | Resend API |

---

## 📊 Database Tables

### MatruRaksha (Existing)

- `mothers` - Mother profiles
- `risk_assessments` - Health assessments
- `chat_history` - Conversation logs
- `user_profiles` - Auth users

### SantanRaksha (New)

- `children` - Child profiles linked to mothers
- `vaccinations` - IAP 2023 vaccine records
- `growth_records` - Weight, height, z-scores
- `milestones` - Developmental achievements
- `postnatal_checkins` - Mother recovery checkups

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - overview |
| [SANTANRAKSHA.md](SANTANRAKSHA.md) | SantanRaksha detailed documentation |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) | Full API reference |

---

## 🚀 Deployment

### Vercel (Frontend)

```bash
# vercel.json already configured
vercel deploy
```

### Render (Backend)

```bash
# render.yaml already configured
# Connect GitHub repo to Render
```

### Environment Variables Needed

- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `RESEND_API_KEY` (optional)

---

## 👥 Team

Built for maternal and child health improvement in underserved communities.

---

## 📝 License

MIT License

---

*Last Updated: January 24, 2026*
