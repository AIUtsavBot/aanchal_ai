# 🗄️ MatruRaksha Database Schema

> Complete database schema documentation for the MatruRaksha AI system using Supabase (PostgreSQL).

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Entity Relationship Diagram](#-entity-relationship-diagram)
- [Core Tables](#-core-tables)
- [Authentication Tables](#-authentication-tables)
- [Healthcare Worker Tables](#-healthcare-worker-tables)
- [Health Tracking Tables](#-health-tracking-tables)
- [Communication Tables](#-communication-tables)
- [Indexes & Performance](#-indexes--performance)
- [Row Level Security (RLS)](#-row-level-security-rls)
- [Triggers & Functions](#-triggers--functions)

---

## 🔍 Overview

The MatruRaksha database is built on PostgreSQL (via Supabase) and consists of:

- **13 Core Tables** for maternal health data
- **Row Level Security (RLS)** for access control
- **Realtime Subscriptions** for live updates
- **Storage Buckets** for document uploads

**Database Connection:**
- Provider: Supabase
- Engine: PostgreSQL 15+
- Features: RLS, Realtime, Edge Functions

---

## 📊 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   auth.users    │       │  user_profiles  │       │registration_    │
│   (Supabase)    │◀──────│                 │       │requests         │
│                 │  1:1  │ • id (uuid, PK) │◀──────│                 │
│ • id (uuid, PK) │       │ • email         │  FK   │ • user_id       │
│ • email         │       │ • full_name     │       │ • role_requested│
│ • ...           │       │ • role          │       │ • status        │
└─────────────────┘       │ • phone         │       └─────────────────┘
                          └────────┬────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │ 1:1                │ 1:1                │
              ▼                    ▼                    │
┌─────────────────┐       ┌─────────────────┐          │
│     doctors     │       │  asha_workers   │          │
│                 │       │                 │          │
│ • id (PK)       │       │ • id (PK)       │          │
│ • user_profile_ │       │ • user_profile_ │          │
│   id (FK)       │       │   id (FK)       │          │
│ • name          │       │ • name          │          │
│ • phone         │       │ • assigned_area │          │
│ • degree_cert_  │       │ • is_active     │          │
│   url           │       └────────┬────────┘          │
└────────┬────────┘                │                   │
         │                         │                   │
         │ 1:N                     │ 1:N               │
         │                         │                   │
         └─────────────┬───────────┘                   │
                       ▼                               │
              ┌─────────────────┐                      │
              │     mothers     │◀─────────────────────┘
              │                 │
              │ • id (PK)       │
              │ • name          │
              │ • phone         │
              │ • age, bmi      │
              │ • doctor_id (FK)│
              │ • asha_worker_  │
              │   id (FK)       │
              │ • telegram_     │
              │   chat_id       │
              └────────┬────────┘
                       │
      ┌────────────────┼────────────────┬──────────────────┐
      │ 1:N            │ 1:N            │ 1:N              │ 1:N
      ▼                ▼                ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│risk_         │ │medical_      │ │health_       │ │appointments  │
│assessments   │ │reports       │ │timeline      │ │              │
│              │ │              │ │              │ │              │
│ • id (PK)    │ │ • id (PK)    │ │ • id (PK)    │ │ • id (PK)    │
│ • mother_id  │ │ • mother_id  │ │ • mother_id  │ │ • mother_id  │
│   (FK)       │ │   (FK)       │ │   (FK)       │ │   (FK)       │
│ • risk_level │ │ • filename   │ │ • event_date │ │ • date       │
│ • risk_score │ │ • analysis   │ │ • event_type │ │ • status     │
│ • bp, hb     │ │ • processed  │ │ • summary    │ │ • notes      │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📌 Core Tables

### `mothers`
Primary table storing mother (patient) information.

```sql
CREATE TABLE public.mothers (
  id            BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  phone         TEXT UNIQUE NOT NULL,
  age           INT,
  gravida       INT,                    -- Number of pregnancies
  parity        INT,                    -- Number of births
  bmi           NUMERIC,
  location      TEXT,
  preferred_language TEXT DEFAULT 'en',
  telegram_chat_id   TEXT,
  doctor_id     BIGINT REFERENCES public.doctors(id),
  asha_worker_id BIGINT REFERENCES public.asha_workers(id),
  medical_history JSONB DEFAULT '{"conditions": [], "medications": [], "trend_analysis": "No prior history."}',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mothers_phone ON public.mothers(phone);
CREATE INDEX idx_mothers_doctor_id ON public.mothers(doctor_id);
CREATE INDEX idx_mothers_asha_worker_id ON public.mothers(asha_worker_id);
CREATE INDEX idx_mothers_telegram ON public.mothers(telegram_chat_id);
```

**Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `name` | TEXT | Mother's full name |
| `phone` | TEXT | Mobile number (unique) |
| `age` | INT | Age in years |
| `gravida` | INT | Total pregnancies |
| `parity` | INT | Number of births |
| `bmi` | NUMERIC | Body Mass Index |
| `location` | TEXT | City/area |
| `preferred_language` | TEXT | Language code (en, hi, ta, etc.) |
| `telegram_chat_id` | TEXT | Telegram user ID |
| `doctor_id` | BIGINT | Assigned doctor (FK) |
| `asha_worker_id` | BIGINT | Assigned ASHA worker (FK) |
| `medical_history` | JSONB | Historical health data |

---

### `risk_assessments`
Stores risk evaluation results.

```sql
CREATE TABLE public.risk_assessments (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mother_id     BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  systolic_bp   INT,
  diastolic_bp  INT,
  hemoglobin    NUMERIC,
  blood_sugar   NUMERIC,
  weight        NUMERIC,
  symptoms      JSONB,
  risk_level    TEXT CHECK (risk_level IN ('HIGH', 'MODERATE', 'LOW')),
  risk_score    INT,
  factors       JSONB,                  -- Contributing risk factors
  recommendations JSONB,                -- AI-generated recommendations
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_assessments_mother_id ON public.risk_assessments(mother_id);
CREATE INDEX idx_risk_assessments_risk_level ON public.risk_assessments(risk_level);
CREATE INDEX idx_risk_assessments_created_at ON public.risk_assessments(created_at);
```

---

## 🔐 Authentication Tables

### `user_profiles`
Links Supabase Auth users to application profiles.

```sql
CREATE TYPE user_role AS ENUM ('ADMIN', 'DOCTOR', 'ASHA_WORKER');

CREATE TABLE public.user_profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email         TEXT UNIQUE NOT NULL,
  full_name     TEXT NOT NULL,
  phone         TEXT,
  role          user_role,              -- NULL = pending approval
  is_active     BOOLEAN DEFAULT TRUE,
  assigned_area TEXT,
  avatar_url    TEXT,
  metadata      JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX idx_user_profiles_role ON public.user_profiles(role);
```

---

### `registration_requests`
Stores pending role requests from OAuth users.

```sql
CREATE TABLE public.registration_requests (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT NOT NULL,
  full_name       TEXT,
  role_requested  TEXT NOT NULL CHECK (role_requested IN ('DOCTOR', 'ASHA_WORKER')),
  degree_cert_url TEXT,                 -- Doctor certificate URL
  status          TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
  reviewed_by     UUID REFERENCES public.user_profiles(id),
  reviewed_at     TIMESTAMPTZ,
  rejection_reason TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

CREATE INDEX idx_registration_requests_status ON public.registration_requests(status);
```

---

## 👩‍⚕️ Healthcare Worker Tables

### `doctors`

```sql
CREATE TABLE public.doctors (
  id              BIGSERIAL PRIMARY KEY,
  user_profile_id UUID REFERENCES public.user_profiles(id),
  name            TEXT NOT NULL,
  email           TEXT,
  phone           TEXT,
  assigned_area   TEXT,
  degree_cert_url TEXT,                 -- Medical registration certificate
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_doctors_user_profile_id ON public.doctors(user_profile_id);
CREATE INDEX idx_doctors_assigned_area ON public.doctors(assigned_area);
```

---

### `asha_workers`

```sql
CREATE TABLE public.asha_workers (
  id              BIGSERIAL PRIMARY KEY,
  user_profile_id UUID REFERENCES public.user_profiles(id),
  name            TEXT NOT NULL,
  email           TEXT,
  phone           TEXT,
  assigned_area   TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_asha_workers_user_profile_id ON public.asha_workers(user_profile_id);
CREATE INDEX idx_asha_workers_assigned_area ON public.asha_workers(assigned_area);
```

---

## 📊 Health Tracking Tables

### `medical_reports`
Stores uploaded medical documents and AI analysis.

```sql
CREATE TABLE public.medical_reports (
  id              BIGSERIAL PRIMARY KEY,
  mother_id       BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  filename        TEXT,
  file_url        TEXT,
  upload_date     TIMESTAMPTZ DEFAULT NOW(),
  analysis_summary TEXT,                -- AI-generated summary
  health_metrics  JSONB,                -- Extracted metrics
  concerns        JSONB,                -- Identified concerns
  recommendations JSONB,                -- AI recommendations
  processed       BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_medical_reports_mother_id ON public.medical_reports(mother_id);
```

---

### `health_timeline`
Tracks health events over pregnancy.

```sql
CREATE TABLE public.health_timeline (
  id            BIGSERIAL PRIMARY KEY,
  mother_id     BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  event_date    DATE NOT NULL,
  event_type    TEXT NOT NULL,          -- check_in, assessment, milestone, etc.
  blood_pressure TEXT,
  hemoglobin    NUMERIC,
  sugar_level   NUMERIC,
  weight        NUMERIC,
  concerns      JSONB,
  summary       TEXT,
  event_data    JSONB,                  -- Additional event-specific data
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_timeline_mother_id ON public.health_timeline(mother_id);
CREATE INDEX idx_health_timeline_event_date ON public.health_timeline(event_date);
```

---

### `appointments`

```sql
CREATE TABLE public.appointments (
  id              BIGSERIAL PRIMARY KEY,
  mother_id       BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  appointment_type TEXT NOT NULL,       -- checkup, ultrasound, lab_test, etc.
  appointment_date TIMESTAMPTZ NOT NULL,
  facility        TEXT,
  notes           TEXT,
  status          TEXT CHECK (status IN ('scheduled', 'confirmed', 'completed', 'missed', 'cancelled')),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_appointments_mother_id ON public.appointments(mother_id);
CREATE INDEX idx_appointments_date ON public.appointments(appointment_date);
CREATE INDEX idx_appointments_status ON public.appointments(status);
```

---

## 💬 Communication Tables

### `case_discussions`
Real-time chat between doctors and ASHA workers.

```sql
CREATE TABLE public.case_discussions (
  id            BIGSERIAL PRIMARY KEY,
  mother_id     BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  sender_role   TEXT NOT NULL CHECK (sender_role IN ('MOTHER', 'ASHA', 'DOCTOR', 'SYSTEM')),
  sender_name   TEXT,
  message       TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_case_discussions_mother_id ON public.case_discussions(mother_id);
CREATE INDEX idx_case_discussions_created_at ON public.case_discussions(created_at);

-- Enable realtime subscriptions
ALTER PUBLICATION supabase_realtime ADD TABLE public.case_discussions;
```

---

### `conversations`
Telegram bot conversation history.

```sql
CREATE TABLE public.conversations (
  id              BIGSERIAL PRIMARY KEY,
  mother_id       BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  message_role    TEXT NOT NULL,        -- user, assistant
  message_content TEXT NOT NULL,
  context_used    JSONB,
  agent_response  JSONB,                -- Which agent handled this
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_mother_id ON public.conversations(mother_id);
```

---

## ⚡ Indexes & Performance

### Critical Indexes

```sql
-- High-traffic queries
CREATE INDEX idx_mothers_phone ON public.mothers(phone);
CREATE INDEX idx_risk_assessments_mother_id ON public.risk_assessments(mother_id);
CREATE INDEX idx_risk_assessments_risk_level ON public.risk_assessments(risk_level);

-- Dashboard aggregations
CREATE INDEX idx_risk_assessments_created_at ON public.risk_assessments(created_at);
CREATE INDEX idx_user_profiles_role ON public.user_profiles(role);

-- Foreign key lookups
CREATE INDEX idx_doctors_user_profile_id ON public.doctors(user_profile_id);
CREATE INDEX idx_asha_workers_user_profile_id ON public.asha_workers(user_profile_id);
```

---

## 🔒 Row Level Security (RLS)

### User Profiles Policies

```sql
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON public.user_profiles FOR SELECT
  USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.user_profiles FOR UPDATE
  USING (auth.uid() = id);

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles"
  ON public.user_profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

-- Admins can update all profiles
CREATE POLICY "Admins can update all profiles"
  ON public.user_profiles FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );
```

---

## ⚙️ Triggers & Functions

### Auto-create User Profile on Signup

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  user_full_name TEXT;
  user_role_enum user_role;
BEGIN
  -- Get name from OAuth metadata or email
  user_full_name := COALESCE(
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'name',
    split_part(NEW.email, '@', 1)
  );
  
  -- Insert user profile (role is NULL = pending approval)
  INSERT INTO public.user_profiles (id, email, full_name, role, is_active)
  VALUES (NEW.id, NEW.email, user_full_name, NULL, TRUE)
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    updated_at = NOW();
    
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

### Auto-update Timestamps

```sql
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
```

---

## 📁 Storage Buckets

```sql
-- Create storage bucket for documents (run via Supabase Dashboard)
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', true);

-- Policy: Authenticated users can upload
CREATE POLICY "Authenticated users can upload documents"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'documents' AND auth.role() = 'authenticated');

-- Policy: Anyone can read documents
CREATE POLICY "Public read access for documents"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'documents');
```

---

## 📚 Related Documentation

- [System Design](./system_design.md)
- [API Endpoints](../api/endpoints.md)
- [Setup Guide](../guides/setup_guide.md)

---

*Last Updated: January 2026*
