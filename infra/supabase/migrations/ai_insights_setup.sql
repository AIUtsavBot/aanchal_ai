
-- AI Insights & Predictions
-- Stores generated insights, risk predictions, and health summaries

CREATE TABLE IF NOT EXISTS patient_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mother_id UUIDREFERENCES mothers(id) ON DELETE CASCADE,
    
    -- TYPE: 'RISK_ASSSESSMENT', 'HEALTH_SUMMARY', 'TREND_ALERT', 'MISSED_VISIT_PREDICTION'
    type TEXT NOT NULL,
    
    -- The core content of the insight
    summary TEXT,
    
    -- Structured data (e.g., specific risk factors, probablistic scores)
    details JSONB,
    
    -- AI Confidence score (0.0 to 1.0)
    confidence_score FLOAT,
    
    -- Severity level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    severity TEXT DEFAULT 'LOW',
    
    -- Metadata
    is_active BOOLEAN DEFAULT true, -- If false, it's a "resolved" or "outdated" insight
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Expiry (optional, for transient predictions)
    valid_until TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_insights_mother ON patient_insights(mother_id);
CREATE INDEX IF NOT EXISTS idx_insights_type ON patient_insights(type);
CREATE INDEX IF NOT EXISTS idx_insights_severity ON patient_insights(severity);

-- RLS Policies (Enable if RLS is on, otherwise optional but good practice)
ALTER TABLE patient_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Doctors and Admins can view insights" 
on patient_insights FOR SELECT 
USING (
  auth.role() = 'authenticated' 
  AND (
    EXISTS (SELECT 1 FROM doctors WHERE id::text = auth.uid()::text) 
    OR 
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role IN ('ADMIN', 'DOCTOR'))
  )
);
