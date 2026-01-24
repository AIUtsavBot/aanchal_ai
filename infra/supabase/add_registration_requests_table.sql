-- =====================================================
-- COMPLETE FIX for Registration Flow
-- Run this in Supabase SQL Editor
-- =====================================================

-- =====================================================
-- 1. CREATE REGISTRATION_REQUESTS TABLE
-- This stores pending signup requests before admin approval
-- =====================================================
CREATE TABLE IF NOT EXISTS public.registration_requests (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  role_requested TEXT NOT NULL CHECK (role_requested IN ('DOCTOR', 'ASHA_WORKER')),
  phone TEXT,
  assigned_area TEXT,
  degree_cert_url TEXT,  -- For doctor certification uploads
  status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
  reviewed_by UUID REFERENCES public.user_profiles(id),
  review_note TEXT,
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_registration_requests_status 
  ON public.registration_requests(status);
CREATE INDEX IF NOT EXISTS idx_registration_requests_email 
  ON public.registration_requests(email);
CREATE INDEX IF NOT EXISTS idx_registration_requests_created_at 
  ON public.registration_requests(created_at DESC);

-- Enable RLS
ALTER TABLE public.registration_requests ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can create a registration request (public endpoint)
DROP POLICY IF EXISTS "Anyone can create registration request" ON public.registration_requests;
CREATE POLICY "Anyone can create registration request"
  ON public.registration_requests FOR INSERT
  WITH CHECK (true);

-- Policy: Users can view their own request by email
DROP POLICY IF EXISTS "Users can view own request" ON public.registration_requests;
CREATE POLICY "Users can view own request"
  ON public.registration_requests FOR SELECT
  USING (email = current_setting('request.jwt.claims', true)::json->>'email');

-- Policy: Admins can view all requests
DROP POLICY IF EXISTS "Admins can view registration requests" ON public.registration_requests;
CREATE POLICY "Admins can view registration requests"
  ON public.registration_requests FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

-- Policy: Admins can update requests (approve/reject)
DROP POLICY IF EXISTS "Admins can update registration requests" ON public.registration_requests;
CREATE POLICY "Admins can update registration requests"
  ON public.registration_requests FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

-- =====================================================
-- 2. ENSURE DOCTORS TABLE HAS REQUIRED COLUMNS
-- =====================================================
ALTER TABLE public.doctors
  ADD COLUMN IF NOT EXISTS user_profile_id UUID REFERENCES public.user_profiles(id),
  ADD COLUMN IF NOT EXISTS email TEXT;

CREATE INDEX IF NOT EXISTS idx_doctors_user_profile_id 
  ON public.doctors(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_doctors_email 
  ON public.doctors(email);

-- =====================================================
-- 3. ENSURE ASHA_WORKERS TABLE HAS REQUIRED COLUMNS
-- =====================================================
ALTER TABLE public.asha_workers
  ADD COLUMN IF NOT EXISTS user_profile_id UUID REFERENCES public.user_profiles(id),
  ADD COLUMN IF NOT EXISTS email TEXT;

CREATE INDEX IF NOT EXISTS idx_asha_workers_user_profile_id 
  ON public.asha_workers(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_asha_workers_email 
  ON public.asha_workers(email);

-- =====================================================
-- 4. CREATE STORAGE BUCKET FOR CERTIFICATIONS
-- Run this separately in Supabase Dashboard > Storage
-- =====================================================
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('certifications', 'certifications', true)
-- ON CONFLICT DO NOTHING;

-- =====================================================
-- VERIFICATION QUERY - Run to check everything is set up
-- =====================================================
-- SELECT 
--   'registration_requests' as table_name, 
--   count(*) as row_count 
-- FROM public.registration_requests
-- UNION ALL
-- SELECT 'user_profiles', count(*) FROM public.user_profiles
-- UNION ALL
-- SELECT 'doctors', count(*) FROM public.doctors
-- UNION ALL
-- SELECT 'asha_workers', count(*) FROM public.asha_workers;

-- =====================================================
-- TABLE DOCUMENTATION
-- =====================================================
COMMENT ON TABLE public.registration_requests IS 
  'Stores pending registration requests from doctors and ASHA workers awaiting admin approval';
COMMENT ON COLUMN public.registration_requests.status IS 
  'Request status: PENDING (awaiting review), APPROVED (user created), REJECTED (denied)';
COMMENT ON COLUMN public.registration_requests.degree_cert_url IS 
  'URL to uploaded certification document (for doctors)';
