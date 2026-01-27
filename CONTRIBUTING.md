
# Contributing to MatruRaksha AI

Thank you for your interest in contributing to MatruRaksha AI! This guide will help you set up your environment and understand our development standards.

## 🚀 Quick Start (Docker)

The easiest way to run the full stack is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-org/santanraksha.git
cd santanraksha

# Start services (API, Redis, Worker, Postgres stub)
docker-compose -f docker-compose.prod.yml up --build -d
```

Access the API at `http://localhost:8000/docs`

## 🛠️ Local Development

### Backend Setup
1. **Python 3.12+** required
2. Create virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure `.env`:
   Copy `.env.example` to `.env` and fill in Supabase credentials.

5. Run server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. **Node.js 18+** required
2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```

## 🧪 Testing
Run backend tests with `pytest`:

```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_postnatal.py
```

**Note**: Integration tests requiring live Supabase are marked `@pytest.mark.integration`.

## 📝 Coding Standards

### Logging
Use our structured logging wrapper. Do NOT use `print()` statements.

```python
from utils.logging_config import logger

logger.info("User logged in", user_id="123", role="doctor")
logger.error("Database connection failed", error=str(e))
```

### Security
- Always use `@audit_action` for sensitive routes (validating user/admin actions).
- Ensure new endpoints have `@audit_action` decorators if they modify data.

## 🚢 Deployment
Push to `main` triggers the CI pipeline which runs tests and builds the Docker image.
Assets are deployed via Render (Backend) and Vercel (Frontend).
