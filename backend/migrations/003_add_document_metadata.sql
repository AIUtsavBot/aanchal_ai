-- Migration to add document_metadata column to registration_requests
-- Run this in Supabase SQL Editor

-- 1. Create table if it doesn't exist (Safety check)
CREATE TABLE IF NOT EXISTS registration_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role_requested TEXT NOT NULL, -- DOCTOR, ASHA_WORKER
    phone TEXT,
    assigned_area TEXT,
    degree_cert_url TEXT,
    password_hash TEXT NOT NULL, -- Encrypted password
    status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    reviewer_note TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID
);

-- 2. Add document_metadata column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'registration_requests' AND column_name = 'document_metadata') THEN
        ALTER TABLE registration_requests ADD COLUMN document_metadata JSONB DEFAULT '{}';
    END IF;
END $$;

-- 3. Enable RLS
ALTER TABLE registration_requests ENABLE ROW LEVEL SECURITY;

-- 4. Policies (Admin only for read/update, Public/Anon for insert)
DROP POLICY IF EXISTS "Public can create registration requests" ON registration_requests;
CREATE POLICY "Public can create registration requests" ON registration_requests
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Admins can view registration requests" ON registration_requests;
CREATE POLICY "Admins can view registration requests" ON registration_requests
    FOR SELECT USING (
        auth.jwt() ->> 'role' = 'service_role' OR
        exists (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'ADMIN')
    );

DROP POLICY IF EXISTS "Admins can update registration requests" ON registration_requests;
CREATE POLICY "Admins can update registration requests" ON registration_requests
    FOR UPDATE USING (
        auth.jwt() ->> 'role' = 'service_role' OR
        exists (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'ADMIN')
    );
