# Project structure — MatruRaksha_AI

This document describes the repository layout, clarifies which files are important for day-to-day development, and contains explicit, actionable steps to clean up committed artifacts and run the project locally.

## Top-level layout

```
maatru-raksha-ai/
├─ README.md                 # Project overview
├─ SETUP.md                  # Setup instructions
├─ PROJECT_STRUCTURE.md      # (this file) annotated layout
├─ backend/                  # Python backend (API, agents, services)
├─ frontend/                 # Web client (Vite + React)
├─ docs/                     # Documentation and guides
├─ infra/                    # Deployment infrastructure (Docker, nginx, supabase)
└─ .gitignore
```

## Detailed backend layout

```
backend/
├─ .env                      # local environment variables (should be in .gitignore and not committed)
├─ requirements.txt          # Python package requirements
├─ package.json              # Node-related tooling for backend (optional)
├─ verify_setup.py           # helper to validate environment
├─ main.py                   # primary application entry point (observed running with `python main.py`)
├─ enhanced_api.py           # alternate API runner or extended endpoints
├─ scheduler.py              # cron/periodic job runner
├─ telegram_bot.py           # bot runner/entrypoint for Telegram integration
├─ agents/                   # domain agents implementing business logic
│  ├─ orchestrator.py
│  ├─ asha_agent.py
│  ├─ care_agent.py
│  ├─ emergency_agent.py
│  ├─ medication_agent.py
│  ├─ nutrition_agent.py
│  └─ risk_agent.py
├─ config/
│  └─ settings.py            # config and environment handling
├─ middleware/
│  └─ auth.py                # auth helpers/middleware
├─ models/
│  ├─ database.py
│  └─ schemas.py             # Pydantic/ORM schemas
├─ services/
│  ├─ auth_service.py        # Authentication and user management
│  ├─ cache_service.py       # In-memory caching with TTL (NEW in v2.3.0)
│  ├─ document_analyzer.py
│  ├─ email_service.py       # Resend email integration
│  ├─ memory_service.py
│  ├─ notification_service.py
│  ├─ supabase_service.py
│  ├─ telegram_service.py
│  └─ voice_service.py
├─ routes/
│  ├─ admin_routes.py        # Admin dashboard endpoints
│  ├─ auth_routes.py         # Authentication endpoints
│  └─ vapi_routes.py         # Voice API endpoints
└─ utils/
   ├─ helpers.py
   └─ validators.py


```

## Frontend layout

```
frontend/
├─ package.json              # frontend dependencies & scripts (Vite + React)
├─ index.html
├─ src/
│  ├─ main.jsx
│  ├─ App.jsx
│  ├─ index.css
│  ├─ components/
│  │  ├─ ChatBot.jsx
│  │  ├─ Dashboard.jsx
│  │  ├─ Navbar.jsx
│  │  ├─ PatientCard.jsx
│  │  └─ RiskChart.jsx
│  ├─ pages/
│  │  ├─ ASHAInterface.jsx
│  │  ├─ Emergency.jsx
│  │  ├─ Home.jsx
│  │  └─ RiskDashboard.jsx
│  └─ services/
│     ├─ api.js
│     └─ telegram.js
└─ .env.local

```

## Infra and docs

```
infra/
├─ docker/
│  ├─ docker-compose.yml
│  ├─ Dockerfile.backend
│  └─ Dockerfile.frontend
├─ nginx/
│  └─ nginx.conf
└─ supabase/
   ├─ schema.sql
   └─ seed.sql

docs/                       # docs grouped by area (api, guides, architecture)
```

## What's updated (delta)

- Added explicit "How to run" instructions for both backend and frontend (including PowerShell-friendly commands).
- Added a recommended `.gitignore` snippet showing lines to add (venv, .env, local db files).
- Expanded the cleanup steps to include exact commands to remove a committed venv from history and how to safely remove it from the current repository state.
- Clarified that `main.py` is the observed entrypoint (the last command run in the workspace was `python main.py`).

## How to run (quick)

Backend (PowerShell, recommended):

```powershell
# from repository root
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Backend (Unix / POSIX):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Frontend (from repository root):

```bash
cd frontend
npm install
npm run dev
```

If your frontend uses `pnpm` or `yarn`, substitute the install/run commands accordingly.

## Recommended `.gitignore` additions

Add the following lines to the top-level `.gitignore` (or to `backend/.gitignore`):

```
# Python virtualenvs
backend/venv*/
backend/.venv/

# Environment files
backend/.env
frontend/.env.local

# Bytecode
**/__pycache__/
*.py[cod]

# IDE/editor
.vscode/
*.swp
```

## How to remove a committed virtualenv (safe, local removal)

If the `backend/venv312/` or any venv was accidentally committed, you can remove it from the latest commit and keep history simple with:

1. Add the entry to `.gitignore` (see recommended additions above).
2. Remove the files and commit the removal:

```powershell
# from repository root (PowerShell)
git rm -r --cached backend/venv312
git commit -m "chore: remove committed virtualenv and ignore it"
git push
```

If the venv was committed across many historical commits and you need to purge it from the repository history (makes a rewritten history), use `git filter-repo` or the BFG repo cleaner. That's a larger operation; ask if you want me to prepare a safe plan.

## Actionable recommendations (prioritized)

1. Add the `.gitignore` entries above and remove the committed `venv312` folder as shown.
2. Move secrets from `backend/.env` to environment variables or a secrets manager and ensure `.env` is ignored.
3. Decide and document the primary backend entrypoint: `main.py` vs `enhanced_api.py` in `README.md`.
4. Add developer scripts in `backend/` (PowerShell script `scripts\setup.ps1` and a small `Makefile` or cross-platform `tasks.json` for VS Code) to standardize setup.
5. Add a minimal CI workflow (GitHub Actions) to run tests and linters on push/PR.

## Quick verification steps

- After adding `.gitignore` and removing the venv, run the backend setup commands above to ensure dependencies install and `python main.py` starts cleanly.
- Run `npm install` and `npm run dev` in `frontend/` to verify the frontend dev server starts.

---

Generated on: 2025-10-19

---

Generated on: 2025-10-19
