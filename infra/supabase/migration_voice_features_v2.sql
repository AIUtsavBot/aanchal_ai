-- Database Setup for Voice-First Consultation Features
-- Run this AFTER running infra/supabase/migration_santanraksha_v1.sql

-- 1. Health Metrics (Vitals History for Mothers)
create table if not exists health_metrics (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  weight_kg numeric,
  blood_pressure_systolic integer,
  blood_pressure_diastolic integer,
  blood_sugar numeric,
  hemoglobin numeric,
  measured_at timestamp with time zone default timezone('utc'::text, now()) not null,
  notes text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Prescriptions Table
create table if not exists prescriptions (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  medication text not null,
  dosage text,
  start_date date,
  end_date date,
  schedule jsonb, -- e.g. {"instructions": "after food"}
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Nutrition Plans
create table if not exists nutrition_plans (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  plan text not null,
  trimester integer,
  language text default 'en',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Appointments
create table if not exists appointments (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  facility text,
  appointment_date timestamp with time zone not null,
  status text default 'scheduled', -- scheduled, completed, cancelled
  appointment_type text, -- consultation, anc, scan
  notes text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 5. Health Timeline (Mother's holistic timeline)
-- Note: 'child_health_timeline' exists for children, this is for mothers
create table if not exists health_timeline (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  event_date date not null,
  event_type text not null, -- doctor_consultation, lab_result, etc.
  event_data jsonb,
  blood_pressure text,
  hemoglobin numeric,
  sugar_level numeric,
  weight numeric,
  summary text,
  concerns jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MIGRATION: Ensure event_date exists if table was created with older schema
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name = 'health_timeline' and column_name = 'event_date') then
        -- Check if 'date' exists (legacy column name)
        if exists (select 1 from information_schema.columns where table_name = 'health_timeline' and column_name = 'date') then
            alter table health_timeline rename column "date" to event_date;
        else
            alter table health_timeline add column event_date date default CURRENT_DATE;
        end if;
    end if;
end $$;

-- 6. Context Memory (Long-term Agent Memory)
create table if not exists context_memory (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  memory_key text not null,
  memory_value text not null,
  memory_type text default 'fact', -- fact, concern, preference, toon
  source text default 'system',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 7. Medical Reports (File Uploads)
create table if not exists medical_reports (
  id uuid default gen_random_uuid() primary key,
  mother_id uuid references mothers(id) on delete cascade not null,
  telegram_chat_id text,
  file_name text,
  file_type text,
  file_url text, -- Storage URL
  file_path text,
  analysis_summary text,
  health_metrics jsonb, -- Extracted vitals
  concerns jsonb, -- List of concerns
  recommendations jsonb, -- List of recommendations
  analysis_raw jsonb,
  analysis_status text default 'pending', -- pending, processing, completed, failed
  uploaded_at timestamp with time zone default timezone('utc'::text, now()) not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for new tables
alter table context_memory enable row level security;
alter table medical_reports enable row level security;

-- Policies
-- Policies
drop policy if exists "Auth users select context_memory" on context_memory;
create policy "Auth users select context_memory" on context_memory for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert context_memory" on context_memory;
create policy "Auth users insert context_memory" on context_memory for insert with check (auth.role() = 'authenticated');

drop policy if exists "Auth users select medical_reports" on medical_reports;
create policy "Auth users select medical_reports" on medical_reports for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert medical_reports" on medical_reports;
create policy "Auth users insert medical_reports" on medical_reports for insert with check (auth.role() = 'authenticated');

-- Enable RLS
alter table health_metrics enable row level security;
alter table prescriptions enable row level security;
alter table nutrition_plans enable row level security;
alter table appointments enable row level security;
alter table health_timeline enable row level security;

-- Simple Policies (Authenticated users access all - refine for production)
drop policy if exists "Auth users select health_metrics" on health_metrics;
create policy "Auth users select health_metrics" on health_metrics for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert health_metrics" on health_metrics;
create policy "Auth users insert health_metrics" on health_metrics for insert with check (auth.role() = 'authenticated');

drop policy if exists "Auth users select prescriptions" on prescriptions;
create policy "Auth users select prescriptions" on prescriptions for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert prescriptions" on prescriptions;
create policy "Auth users insert prescriptions" on prescriptions for insert with check (auth.role() = 'authenticated');

drop policy if exists "Auth users select nutrition_plans" on nutrition_plans;
create policy "Auth users select nutrition_plans" on nutrition_plans for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert nutrition_plans" on nutrition_plans;
create policy "Auth users insert nutrition_plans" on nutrition_plans for insert with check (auth.role() = 'authenticated');

drop policy if exists "Auth users select appointments" on appointments;
create policy "Auth users select appointments" on appointments for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert appointments" on appointments;
create policy "Auth users insert appointments" on appointments for insert with check (auth.role() = 'authenticated');

drop policy if exists "Auth users select health_timeline" on health_timeline;
create policy "Auth users select health_timeline" on health_timeline for select using (auth.role() = 'authenticated');

drop policy if exists "Auth users insert health_timeline" on health_timeline;
create policy "Auth users insert health_timeline" on health_timeline for insert with check (auth.role() = 'authenticated');

-- Performance Indexes
create index if not exists idx_health_metrics_mother_date on health_metrics(mother_id, measured_at desc);
create index if not exists idx_prescriptions_mother on prescriptions(mother_id);
create index if not exists idx_appointments_mother_date on appointments(mother_id, appointment_date);
create index if not exists idx_timeline_mother_date on health_timeline(mother_id, event_date desc);
create index if not exists idx_context_memory_mother_created on context_memory(mother_id, created_at desc);
create index if not exists idx_medical_reports_mother_uploaded on medical_reports(mother_id, uploaded_at desc);

