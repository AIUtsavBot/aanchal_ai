# 🏗️ MatruRaksha Infrastructure

> Configuration files for deploying MatruRaksha AI to various environments.

---

## 📁 Directory Structure

```
infra/
├── docker/                    # Docker configuration
│   ├── docker-compose.yml     # Multi-service orchestration
│   ├── Dockerfile.backend     # Backend container image
│   └── Dockerfile.frontend    # Frontend container image
│
├── nginx/                     # Reverse proxy
│   └── nginx.conf             # Nginx configuration
│
├── supabase/                  # Database
│   ├── schema.sql             # Main database schema
│   ├── seed.sql               # Sample/test data
│   ├── add_registration_requests_table.sql
│   └── fix_oauth_trigger.sql
│
└── env_examples/              # Environment templates
    ├── .env.example           # Backend environment vars
    └── .env.local.example     # Frontend environment vars
```

---

## 🐳 Docker Deployment

### Quick Start

```bash
cd infra/docker

# Create environment file
cp ../env_examples/.env.example .env
# Edit .env with your credentials

# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | React SPA (via Nginx) |
| `scheduler` | - | Background task runner |

---

## 🌐 Nginx Configuration

The `nginx.conf` provides:

- **Reverse Proxy** - Routes `/api/` to backend
- **SPA Routing** - Fallback to `index.html`
- **Security Headers** - XSS, clickjacking protection
- **Gzip Compression** - Reduced bandwidth
- **Rate Limiting** - API abuse prevention
- **Static Caching** - 1-year cache for assets

---

## 🗄️ Database Schema

The `supabase/schema.sql` contains:

- All table definitions
- Indexes for performance
- Row Level Security (RLS) policies
- Triggers for auto-timestamps
- User profile creation trigger

### Run Migrations

1. Open Supabase Dashboard → SQL Editor
2. Copy contents of `schema.sql`
3. Click **Run**

---

## 🔧 Environment Variables

Copy templates before use:

```bash
# Backend
cp env_examples/.env.example ../backend/.env

# Frontend
cp env_examples/.env.local.example ../frontend/.env.local
```

See each file for detailed documentation of all variables.

---

## 📚 Related Documentation

- [Deployment Guide](../docs/guides/deployment_guide.md)
- [Setup Guide](../docs/guides/setup_guide.md)
- [Database Schema](../docs/architecture/database_schema.md)

---

*Last Updated: January 2026*
