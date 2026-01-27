
-- Webhooks for external integration
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL, -- e.g. ['assessment.created', 'high_risk.detected']
    secret TEXT NOT NULL, -- for signing payload
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    webhook_id UUID REFERENCES webhooks(id) ON DELETE CASCADE,
    event TEXT NOT NULL,
    status INTEGER, -- HTTP status code
    response TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks(is_active);
