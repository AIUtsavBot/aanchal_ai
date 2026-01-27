
-- Audit Logging System
-- Tracks who did what, when, and from where (IP)

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,           -- e.g., 'USER_LOGIN', 'VIEW_RECORD', 'EXPORT_DATA'
    actor_id UUID,                  -- User who performed the action (nullable for system actions)
    actor_role TEXT,                -- Role at the time of action (ADMIN, DOCTOR, etc.)
    target_resource TEXT,           -- Table or Resource being accessed (e.g., 'mothers', 'vaccinations')
    target_id TEXT,                 -- Specific record ID
    details JSONB,                  -- Additional context (e.g., changed fields, query params)
    ip_address INET,                -- IP address of the request
    user_agent TEXT,                -- User Agent string
    status TEXT DEFAULT 'SUCCESS',  -- SUCCESS, FAILURE, DENIED
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast searching and filtering
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_resource, target_id);

-- Optional: Partitioning could be added here for scale, but keeping it simple for now.
