# MatruRaksha AI - Database Schema

> Complete database schema documentation for Supabase PostgreSQL

---

## Entity Relationship Diagram

```
                         ┌─────────────────────┐
                         │    user_profiles    │
                         │─────────────────────│
                         │ id (uuid, PK)       │
                         │ email               │
                         │ full_name           │
                         │ role (enum)         │
                         │ is_active           │
                         │ assigned_area       │
                         └─────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│      doctors        │  │    asha_workers     │  │registration_requests│
│─────────────────────│  │─────────────────────│  │─────────────────────│
│ id (serial, PK)     │  │ id (serial, PK)     │  │ id (serial, PK)     │
│ name                │  │ name                │  │ email               │
│ phone               │  │ phone               │  │ role_requested      │
│ assigned_area       │  │ assigned_area       │  │ status (enum)       │
│ user_profile_id(FK) │  │ user_profile_id(FK) │  │ degree_cert_url     │
└─────────┬───────────┘  └─────────┬───────────┘  └─────────────────────┘
          │                        │
          └──────────┬─────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │      mothers        │
            │─────────────────────│
            │ id (serial, PK)     │
            │ name                │
            │ phone (unique)      │
            │ age, bmi, gravida   │
            │ parity, location    │
            │ telegram_chat_id    │
            │ doctor_id (FK)      │
            │ asha_worker_id (FK) │
            └─────────┬───────────┘
                      │
     ┌────────────────┼────────────────┬─────────────────┐
     │                │                │                 │
     ▼                ▼                ▼                 ▼
┌──────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐
│health_   │  │medical_      │  │appointments │  │context_    │
│timeline  │  │reports       │  │             │  │memory      │
└──────────┘  └──────────────┘  └─────────────┘  └────────────┘
```

---

## Core Tables

### 1. `mothers`
Primary table for pregnant mother profiles.

```sql
CREATE TABLE public.mothers (
  id            BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  phone         TEXT UNIQUE NOT NULL,
  age           INT,
  gravida       INT,                    -- Number of pregnancies
  parity        INT,                    -- Number of live births
  bmi           NUMERIC,
  location      TEXT,
  preferred_language TEXT DEFAULT 'en',
  telegram_chat_id   TEXT,              -- Linked Telegram account
  due_date      DATE,
  medical_history    JSONB DEFAULT '{"conditions": [], "medications": [], "trend_analysis": "No prior history."}',
  asha_worker_id     BIGINT REFERENCES public.asha_workers(id),
  doctor_id          BIGINT REFERENCES public.doctors(id),
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mothers_phone ON public.mothers(phone);
CREATE INDEX idx_mothers_telegram ON public.mothers(telegram_chat_id);
CREATE INDEX idx_mothers_location ON public.mothers(location);
```

---

### 2. `doctors`
Healthcare providers (doctors) who can be assigned to mothers.

```sql
CREATE TABLE public.doctors (
  id              BIGSERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  phone           TEXT,
  email           TEXT,
  assigned_area   TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  user_profile_id UUID REFERENCES public.user_profiles(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_doctors_area ON public.doctors(assigned_area);
CREATE INDEX idx_doctors_user_profile ON public.doctors(user_profile_id);
```

---

### 3. `asha_workers`
Community health workers who directly interact with mothers.

```sql
CREATE TABLE public.asha_workers (
  id              BIGSERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  phone           TEXT,
  email           TEXT,
  assigned_area   TEXT,
  is_active       BOOLEAN DEFAULT TRUE,
  user_profile_id UUID REFERENCES public.user_profiles(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_asha_workers_area ON public.asha_workers(assigned_area);
CREATE INDEX idx_asha_workers_user_profile ON public.asha_workers(user_profile_id);
```

---

## Health Tracking Tables

### 4. `health_timeline`
Chronological health events for each mother.

```sql
CREATE TABLE public.health_timeline (
  id            BIGSERIAL PRIMARY KEY,
  mother_id     BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  event_date    DATE NOT NULL,
  event_type    TEXT NOT NULL,          -- 'checkup', 'report_upload', 'emergency'
  blood_pressure TEXT,                   -- e.g., "120/80"
  hemoglobin    NUMERIC,
  sugar_level   NUMERIC,
  weight        NUMERIC,
  concerns      JSONB,                   -- Array of concern strings
  summary       TEXT,
  event_data    JSONB,                   -- Additional event-specific data
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_timeline_mother_id ON public.health_timeline(mother_id);
CREATE INDEX idx_timeline_event_date ON public.health_timeline(event_date);
```

---

### 5. `medical_reports`
Uploaded medical documents with AI analysis results.

```sql
CREATE TABLE public.medical_reports (
  id               BIGSERIAL PRIMARY KEY,
  mother_id        BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  telegram_chat_id TEXT,
  file_name        TEXT,
  file_url         TEXT,
  file_path        TEXT,
  file_type        TEXT,                 -- MIME type
  uploaded_at      TIMESTAMPTZ,
  analysis_status  TEXT DEFAULT 'pending',  -- pending, processing, completed, error
  analysis_result  JSONB,                -- Full AI analysis output
  extracted_metrics JSONB,               -- Parsed health metrics
  error_message    TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_mother_id ON public.medical_reports(mother_id);
CREATE INDEX idx_reports_status ON public.medical_reports(analysis_status);
```

---

### 6. `health_metrics`
Individual health metric recordings.

```sql
CREATE TABLE public.health_metrics (
  id                      BIGSERIAL PRIMARY KEY,
  mother_id               BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  weight_kg               NUMERIC,
  blood_pressure_systolic INT,
  blood_pressure_diastolic INT,
  hemoglobin              NUMERIC,
  blood_sugar             NUMERIC,
  measured_at             TIMESTAMPTZ,
  notes                   TEXT,
  created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_mother_id ON public.health_metrics(mother_id);
CREATE INDEX idx_metrics_measured_at ON public.health_metrics(measured_at);
```

---

### 7. `appointments`
Scheduled healthcare appointments.

```sql
CREATE TABLE public.appointments (
  id               BIGSERIAL PRIMARY KEY,
  mother_id        BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  appointment_type TEXT NOT NULL,        -- 'checkup', 'ultrasound', 'vaccination'
  appointment_date TIMESTAMPTZ NOT NULL,
  facility         TEXT,
  notes            TEXT,
  status           TEXT,                 -- scheduled, confirmed, completed, missed, cancelled
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT chk_appointments_status 
    CHECK (status IN ('scheduled', 'confirmed', 'completed', 'missed', 'cancelled'))
);

CREATE INDEX idx_appointments_mother_id ON public.appointments(mother_id);
CREATE INDEX idx_appointments_date ON public.appointments(appointment_date);
```

---

## AI & Conversation Tables

### 8. `context_memory`
Persistent memory for AI context.

```sql
CREATE TABLE public.context_memory (
  id           BIGSERIAL PRIMARY KEY,
  mother_id    BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  memory_key   TEXT NOT NULL,
  memory_value TEXT NOT NULL,
  memory_type  TEXT,                    -- 'preference', 'medical', 'interaction'
  source       TEXT,                    -- Where the memory was captured
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_context_memory_mother_id ON public.context_memory(mother_id);
CREATE INDEX idx_context_memory_key ON public.context_memory(memory_key);
```

---

### 9. `conversations`
Chat history for AI agent interactions.

```sql
CREATE TABLE public.conversations (
  id              BIGSERIAL PRIMARY KEY,
  mother_id       BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  message_role    TEXT NOT NULL,         -- 'user', 'assistant', 'system'
  message_content TEXT NOT NULL,
  context_used    JSONB,                 -- Context provided to AI
  agent_response  JSONB,                 -- Full agent response metadata
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_mother_id ON public.conversations(mother_id);
CREATE INDEX idx_conversations_created ON public.conversations(created_at);
```

---

### 10. `case_discussions`
Multi-party case discussions (Mother, ASHA, Doctor).

```sql
CREATE TABLE public.case_discussions (
  id           BIGSERIAL PRIMARY KEY,
  mother_id    BIGINT REFERENCES public.mothers(id) ON DELETE CASCADE,
  sender_role  TEXT NOT NULL,            -- MOTHER, ASHA, DOCTOR, SYSTEM
  sender_name  TEXT,
  message      TEXT NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT chk_case_discussions_sender_role 
    CHECK (sender_role IN ('MOTHER', 'ASHA', 'DOCTOR', 'SYSTEM'))
);

-- Realtime enabled for live chat
ALTER PUBLICATION supabase_realtime ADD TABLE public.case_discussions;
```

---

## Authentication Tables

### 11. `user_profiles`
Extended user profiles linked to Supabase Auth.

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
  metadata      JSONB DEFAULT '{}'::JSONB,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX idx_user_profiles_role ON public.user_profiles(role);
```

---

### 12. `registration_requests`
Admin approval queue for new user registrations.

```sql
CREATE TABLE public.registration_requests (
  id               BIGSERIAL PRIMARY KEY,
  email            TEXT NOT NULL UNIQUE,
  full_name        TEXT NOT NULL,
  role_requested   TEXT NOT NULL,
  phone            TEXT,
  assigned_area    TEXT,
  degree_cert_url  TEXT,                -- For doctor certifications
  status           TEXT NOT NULL DEFAULT 'PENDING',
  reviewed_by      UUID REFERENCES public.user_profiles(id),
  review_note      TEXT,
  reviewed_at      TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT chk_role CHECK (role_requested IN ('DOCTOR', 'ASHA_WORKER')),
  CONSTRAINT chk_status CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED'))
);

CREATE INDEX idx_registration_requests_status ON public.registration_requests(status);
CREATE INDEX idx_registration_requests_email ON public.registration_requests(email);
```

---

## Row Level Security (RLS) Policies

```sql
-- Enable RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registration_requests ENABLE ROW LEVEL SECURITY;

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

-- Admins can manage registration requests
CREATE POLICY "Admins can manage all requests"
  ON public.registration_requests FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );
```

---

## Database Functions & Triggers

### Auto-create User Profile on Sign Up

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  user_full_name TEXT;
  user_role_value TEXT;
  user_role_enum user_role;
BEGIN
  -- Get full name from metadata
  user_full_name := COALESCE(
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'name',
    split_part(NEW.email, '@', 1)
  );
  
  -- Get role from metadata
  user_role_value := NEW.raw_user_meta_data->>'role';
  
  IF user_role_value IN ('ADMIN', 'DOCTOR', 'ASHA_WORKER') THEN
    user_role_enum := user_role_value::user_role;
  ELSE
    user_role_enum := NULL;  -- Pending approval
  END IF;

  INSERT INTO public.user_profiles (id, email, full_name, role, is_active)
  VALUES (NEW.id, NEW.email, user_full_name, user_role_enum, TRUE)
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    updated_at = NOW();
    
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## Storage Buckets

```sql
-- Medical reports storage
INSERT INTO storage.buckets (id, name, public) 
VALUES ('medical-reports', 'medical-reports', true);

-- Degree certificates for doctor verification
INSERT INTO storage.buckets (id, name, public) 
VALUES ('documents', 'documents', true);
```

---

*Last updated: January 2026*
