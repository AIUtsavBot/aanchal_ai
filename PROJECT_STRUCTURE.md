# 📁 Project Structure — MatruRaksha AI

> Annotated repository layout with file descriptions and development guidelines.

---

## 📋 Table of Contents

- [Top-Level Layout](#top-level-layout)
- [Backend Structure](#backend-structure)
- [Frontend Structure](#frontend-structure)
- [Documentation Structure](#documentation-structure)
- [Infrastructure](#infrastructure)
- [How to Run](#how-to-run)
- [Recommended .gitignore](#recommended-gitignore)
- [Development Guidelines](#development-guidelines)

---

## Top-Level Layout

```
matruraksha-ai/
├── 📄 README.md                 # Project overview and features
├── 📄 CHANGELOG.md              # Version history and changes
├── 📄 PROJECT_STRUCTURE.md      # This file - repository layout
├── 📄 render.yaml               # Render deployment config
├── 📄 vercel.json               # Vercel deployment config
├── 📄 .gitignore                # Git ignore rules
│
├── 📂 backend/                  # Python FastAPI backend
├── 📂 frontend/                 # React Vite frontend
├── 📂 docs/                     # Documentation
└── 📂 infra/                    # Infrastructure configs
```

---

## Backend Structure

```
backend/
├── 📄 main.py                   # 🚀 Primary application entry point (FastAPI)
├── 📄 telegram_bot.py           # Telegram bot runner/handlers
├── 📄 scheduler.py              # Cron/periodic job runner
├── 📄 enhanced_api.py           # Extended API routes (/api/v1/...)
├── 📄 context_builder.py        # AI context building utilities
│
├── 📄 requirements.txt          # Python dependencies
├── 📄 Dockerfile                # Container image definition
├── 📄 Procfile                  # Render/Heroku process file
├── 📄 runtime.txt               # Python version specification
├── 📄 .env.example              # Environment variables template
│
├── 📂 agents/                   # 🤖 AI Agent System
│   ├── __init__.py              # Agent exports
│   ├── base_agent.py            # Abstract base agent class
│   ├── orchestrator.py          # Agent routing and coordination
│   ├── risk_agent.py            # Risk assessment agent
│   ├── emergency_agent.py       # Emergency detection agent
│   ├── care_agent.py            # Care planning agent
│   ├── nutrition_agent.py       # Nutrition advice agent
│   ├── medication_agent.py      # Medication management agent
│   └── asha_agent.py            # ASHA worker coordination
│
├── 📂 routes/                   # API Route Handlers
│   ├── auth_routes.py           # Authentication endpoints
│   ├── admin_routes.py          # Admin dashboard endpoints
│   └── vapi_routes.py           # Voice AI (Vapi) endpoints
│
├── 📂 services/                 # Business Logic Services
│   ├── __init__.py
│   ├── auth_service.py          # User authentication logic
│   ├── cache_service.py         # In-memory TTL caching (v2.3.0)
│   ├── supabase_service.py      # Database operations
│   ├── email_service.py         # Resend email integration
│   ├── sms_service.py           # Fast2SMS/Twilio integration
│   ├── telegram_service.py      # Telegram message handling
│   ├── document_analyzer.py     # Gemini document analysis
│   ├── memory_service.py        # Conversation memory
│   ├── notification_service.py  # Alert notifications
│   └── voice_service.py         # Voice call management
│
├── 📂 middleware/               # Request Middleware
│   └── auth.py                  # JWT verification middleware
│
├── 📂 models/                   # Data Models
│   ├── database.py              # Supabase client setup
│   └── schemas.py               # Pydantic request/response models
│
├── 📂 config/                   # Configuration
│   └── settings.py              # Environment and app settings
│
├── 📂 utils/                    # Utility Functions
│   ├── helpers.py               # General helper functions
│   └── validators.py            # Input validation utilities
│
├── 📂 scripts/                  # Utility Scripts
│   └── ...                      # Database scripts, migrations
│
└── 📄 verify_setup.py           # Environment validation script
```

### Key Entry Points

| File | Purpose | Command |
|------|---------|---------|
| `main.py` | Primary API server | `python main.py` |
| `telegram_bot.py` | Telegram bot | `python telegram_bot.py` |
| `scheduler.py` | Scheduled tasks | `python scheduler.py` |

---

## Frontend Structure

```
frontend/
├── 📄 index.html                # HTML entry point
├── 📄 package.json              # Node dependencies and scripts
├── 📄 package-lock.json         # Locked dependency versions
├── 📄 vite.config.js            # Vite bundler configuration
├── 📄 tailwind.config.js        # Tailwind CSS configuration
├── 📄 postcss.config.js         # PostCSS configuration
├── 📄 Dockerfile                # Container image definition
├── 📄 vercel.json               # Vercel SPA routing
│
├── 📂 src/
│   ├── 📄 main.jsx              # React entry point
│   ├── 📄 App.jsx               # Main app component with routing
│   ├── 📄 index.css             # Global styles
│   ├── 📄 i18n.js               # Internationalization setup
│   │
│   ├── 📂 pages/                # Route-Level Components
│   │   ├── Home.jsx             # Landing page
│   │   ├── Login.jsx            # Login page
│   │   ├── Signup.jsx           # Registration page
│   │   ├── AuthCallback.jsx     # OAuth callback handler
│   │   ├── RiskDashboard.jsx    # Risk monitoring dashboard
│   │   ├── DoctorDashboard.jsx  # Doctor patient management
│   │   ├── ASHAInterface.jsx    # ASHA worker interface
│   │   ├── AdminDashboard.jsx   # Admin portal
│   │   ├── AdminApprovals.jsx   # User approval center
│   │   └── Emergency.jsx        # Emergency page
│   │
│   ├── 📂 components/           # Reusable UI Components
│   │   ├── Navbar.jsx           # Navigation header
│   │   ├── PatientCard.jsx      # Patient summary card
│   │   ├── RiskChart.jsx        # Risk visualization
│   │   ├── CaseChat.jsx         # Real-time chat component
│   │   ├── Dashboard.jsx        # Dashboard layout
│   │   ├── ChatBot.jsx          # Chatbot interface
│   │   └── ProtectedRoute.jsx   # Route authorization
│   │
│   ├── 📂 contexts/             # React Context Providers
│   │   └── AuthContext.jsx      # Authentication state
│   │
│   ├── 📂 services/             # API Integration
│   │   ├── api.js               # Axios HTTP client
│   │   ├── auth.js              # Supabase Auth wrapper
│   │   └── telegram.js          # Telegram integration
│   │
│   ├── 📂 styles/               # CSS Modules/Styles
│   │   └── ...
│   │
│   ├── 📂 utils/                # Utility Functions
│   │   └── ...
│   │
│   └── 📂 assets/               # Static Assets
│       └── ...
│
└── 📂 dist/                     # Production build output
```

---

## Documentation Structure

```
docs/
├── 📄 README.md                 # Documentation index
│
├── 📂 api/                      # API Documentation
│   ├── endpoints.md             # REST API reference
│   └── telegram_endpoints.md    # Telegram bot API
│
├── 📂 architecture/             # System Architecture
│   ├── system_design.md         # High-level design
│   └── database_schema.md       # Database structure
│
├── 📂 guides/                   # Setup & Deployment Guides
│   ├── setup_guide.md           # Local development setup
│   └── deployment_guide.md      # Production deployment
│
└── 📂 telegram/                 # Telegram Bot Docs
    ├── bot_commands.md          # Command reference
    └── telegram_setup.md        # Bot configuration
```

---

## Infrastructure

```
infra/
├── 📂 docker/                   # Docker Configuration
│   ├── docker-compose.yml       # Multi-service orchestration
│   ├── Dockerfile.backend       # Backend container
│   └── Dockerfile.frontend      # Frontend container
│
├── 📂 nginx/                    # Reverse Proxy
│   └── nginx.conf               # Nginx configuration
│
├── 📂 supabase/                 # Database
│   ├── schema.sql               # Main database schema
│   ├── seed.sql                 # Sample data
│   ├── add_registration_requests_table.sql
│   └── fix_oauth_trigger.sql
│
└── 📂 env_examples/             # Environment Templates
    ├── .env.example             # Backend env template
    └── .env.local.example       # Frontend env template
```

---

## How to Run

### Backend (PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Backend (Unix/macOS)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cd infra/docker
docker-compose up -d --build
```

---

## Recommended .gitignore

Add these to your `.gitignore`:

```gitignore
# Python
backend/venv/
backend/.venv/
**/__pycache__/
*.py[cod]

# Node
frontend/node_modules/
frontend/dist/

# Environment files
backend/.env
frontend/.env.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## Development Guidelines

### Code Style

| Language | Style Guide | Linter |
|----------|-------------|--------|
| Python | PEP 8 | `flake8`, `black` |
| JavaScript | ESLint Recommended | `eslint` |
| TypeScript | TypeScript Strict | `typescript` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new risk assessment endpoint
fix: resolve CORS issue on production
docs: update API documentation
chore: upgrade dependencies
```

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `develop` | Integration branch |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation updates |

---

## Quick Verification

After setup, verify everything works:

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend dev server
# Open http://localhost:5173

# API documentation
# Open http://localhost:8000/docs
```

---

*Last Updated: January 2026*
