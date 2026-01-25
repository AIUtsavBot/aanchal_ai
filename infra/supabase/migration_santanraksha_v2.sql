-- ============================================================
-- SantanRaksha Database Migration v2
-- File: migration_santanraksha_v2.sql
-- Date: 2026-01-25
--
-- This migration ensures all required columns exist for:
-- 1. Vaccinations tracking (IAP 2023 schedule)
-- 2. Growth monitoring (WHO z-scores)
-- 3. Developmental milestones (RBSK 4Ds)
-- ============================================================

-- ==================== VACCINATIONS TABLE ====================
-- The vaccinations table should already exist from the base schema
-- These are optional additions/updates if needed

-- Add reminder tracking columns if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'vaccinations' AND column_name = 'reminder_sent_at') THEN
        ALTER TABLE vaccinations ADD COLUMN reminder_sent_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'vaccinations' AND column_name = 'reminder_count') THEN
        ALTER TABLE vaccinations ADD COLUMN reminder_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create index for faster vaccination queries
CREATE INDEX IF NOT EXISTS idx_vaccinations_child_status 
    ON vaccinations(child_id, status);

CREATE INDEX IF NOT EXISTS idx_vaccinations_due_date 
    ON vaccinations(due_date) WHERE status != 'completed';


-- ==================== GROWTH RECORDS TABLE ====================
-- The growth_records table should already exist from the base schema
-- These ensure all required columns exist

-- Add measurement_location if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'growth_records' AND column_name = 'measurement_location') THEN
        ALTER TABLE growth_records ADD COLUMN measurement_location TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'growth_records' AND column_name = 'alert_generated') THEN
        ALTER TABLE growth_records ADD COLUMN alert_generated BOOLEAN DEFAULT false;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'growth_records' AND column_name = 'muac_cm') THEN
        ALTER TABLE growth_records ADD COLUMN muac_cm NUMERIC;
    END IF;
END $$;

-- Create indexes for growth tracking
CREATE INDEX IF NOT EXISTS idx_growth_records_child_date 
    ON growth_records(child_id, measurement_date DESC);

CREATE INDEX IF NOT EXISTS idx_growth_records_status 
    ON growth_records(growth_status) WHERE growth_status IN ('moderate_acute_malnutrition', 'severe_acute_malnutrition');


-- ==================== MILESTONES TABLE ====================
-- The milestones table should already exist from the base schema
-- These ensure all required columns exist

-- Add any missing columns
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'milestones' AND column_name = 'is_delayed') THEN
        ALTER TABLE milestones ADD COLUMN is_delayed BOOLEAN DEFAULT false;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'milestones' AND column_name = 'delay_in_months') THEN
        ALTER TABLE milestones ADD COLUMN delay_in_months INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'milestones' AND column_name = 'referral_needed') THEN
        ALTER TABLE milestones ADD COLUMN referral_needed BOOLEAN DEFAULT false;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'milestones' AND column_name = 'referral_date') THEN
        ALTER TABLE milestones ADD COLUMN referral_date DATE;
    END IF;
END $$;

-- Create indexes for milestone queries
CREATE INDEX IF NOT EXISTS idx_milestones_child_achieved 
    ON milestones(child_id, is_achieved) WHERE is_achieved = true;

CREATE INDEX IF NOT EXISTS idx_milestones_category 
    ON milestones(category);


-- ==================== FEEDING RECORDS TABLE ====================
-- Add missing columns if needed

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'feeding_records' AND column_name = 'minimum_dietary_diversity_met') THEN
        ALTER TABLE feeding_records ADD COLUMN minimum_dietary_diversity_met BOOLEAN;
    END IF;
END $$;


-- ==================== POSTNATAL ASSESSMENTS TABLE ====================
-- This table stores postnatal health assessments for both mothers and children

CREATE TABLE IF NOT EXISTS postnatal_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID REFERENCES mothers(id) ON DELETE CASCADE,
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    assessor_id TEXT, -- Changed from UUID to TEXT to support both UUIDs (users) and BigInts (doctors/asha)
    assessor_role TEXT CHECK (assessor_role = ANY (ARRAY['asha'::text, 'anm'::text, 'doctor'::text, 'nurse'::text])),
    assessment_type TEXT NOT NULL CHECK (assessment_type = ANY (ARRAY['mother_postnatal'::text, 'child_checkup'::text, 'combined'::text])),
    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    days_postpartum INTEGER,
    age_days INTEGER,
    temperature NUMERIC,
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    pulse_rate INTEGER,
    
    -- Postnatal Recovery (Mother)
    uterine_involution TEXT CHECK (uterine_involution = ANY (ARRAY['normal'::text, 'subinvolution'::text, 'tender'::text])),
    lochia_status TEXT CHECK (lochia_status = ANY (ARRAY['normal'::text, 'foul_smelling'::text, 'excessive'::text, 'absent'::text])),
    episiotomy_wound TEXT CHECK (episiotomy_wound = ANY (ARRAY['healing_well'::text, 'infected'::text, 'dehisced'::text, 'not_applicable'::text])),
    cesarean_wound TEXT CHECK (cesarean_wound = ANY (ARRAY['healing_well'::text, 'infected'::text, 'dehisced'::text, 'not_applicable'::text])),
    breast_condition TEXT CHECK (breast_condition = ANY (ARRAY['normal'::text, 'engorged'::text, 'cracked_nipples'::text, 'mastitis'::text])),
    breastfeeding_established BOOLEAN DEFAULT true,
    
    -- Mental Health (Mother)
    mood_status TEXT CHECK (mood_status = ANY (ARRAY['stable'::text, 'anxious'::text, 'sad'::text, 'overwhelmed'::text])),
    sleep_quality TEXT CHECK (sleep_quality = ANY (ARRAY['adequate'::text, 'poor'::text, 'insomnia'::text])),
    postpartum_depression_risk TEXT CHECK (postpartum_depression_risk = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text])),
    bonding_with_baby TEXT CHECK (bonding_with_baby = ANY (ARRAY['good'::text, 'developing'::text, 'poor'::text])),
    
    -- Danger Signs (Mother)
    fever BOOLEAN DEFAULT false,
    excessive_bleeding BOOLEAN DEFAULT false,
    foul_discharge BOOLEAN DEFAULT false,
    breast_engorgement BOOLEAN DEFAULT false,
    mastitis BOOLEAN DEFAULT false,
    urinary_issues BOOLEAN DEFAULT false,
    
    -- Child Measurements
    weight_kg NUMERIC,
    length_cm NUMERIC,
    head_circumference_cm NUMERIC,
    
    -- Child Vital Signs
    child_temperature NUMERIC,
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    
    -- Child Feeding
    feeding_type TEXT CHECK (feeding_type = ANY (ARRAY['exclusive_breastfeeding'::text, 'mixed'::text, 'formula'::text, 'complementary'::text])),
    feeding_frequency TEXT,
    feeding_issues TEXT[],
    
    -- Child Physical Examination
    skin_color TEXT CHECK (skin_color = ANY (ARRAY['normal'::text, 'pale'::text, 'cyanotic'::text, 'jaundiced'::text])),
    jaundice_level TEXT CHECK (jaundice_level = ANY (ARRAY['none'::text, 'mild_face'::text, 'moderate'::text, 'severe'::text])),
    umbilical_cord TEXT CHECK (umbilical_cord = ANY (ARRAY['clean_dry'::text, 'moist'::text, 'infected'::text, 'separated'::text])),
    fontanelle TEXT CHECK (fontanelle = ANY (ARRAY['normal'::text, 'bulging'::text, 'sunken'::text])),
    eyes TEXT CHECK (eyes = ANY (ARRAY['normal'::text, 'discharge'::text, 'swelling'::text])),
    reflexes TEXT CHECK (reflexes = ANY (ARRAY['present'::text, 'weak'::text, 'absent'::text])),
    muscle_tone TEXT CHECK (muscle_tone = ANY (ARRAY['normal'::text, 'hypotonic'::text, 'hypertonic'::text])),
    
    -- IMNCI Danger Signs (Child)
    not_feeding_well BOOLEAN DEFAULT false,
    convulsions BOOLEAN DEFAULT false,
    fast_breathing BOOLEAN DEFAULT false,
    chest_indrawing BOOLEAN DEFAULT false,
    high_fever BOOLEAN DEFAULT false,
    hypothermia BOOLEAN DEFAULT false,
    jaundice_extending BOOLEAN DEFAULT false,
    umbilical_infection BOOLEAN DEFAULT false,
    
    -- Risk Assessment
    overall_risk_level TEXT CHECK (overall_risk_level = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
    referral_needed BOOLEAN DEFAULT false,
    referral_reason TEXT,
    referral_facility TEXT,
    
    -- Notes & Follow-up
    notes TEXT,
    recommendations TEXT,
    next_visit_date DATE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== POSTNATAL CHECKINS TABLE ====================
CREATE TABLE IF NOT EXISTS postnatal_checkins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mother_id UUID REFERENCES mothers(id) NOT NULL,
  checkin_date DATE NOT NULL,
  days_postpartum INTEGER NOT NULL,
  bleeding_status TEXT CHECK (bleeding_status = ANY (ARRAY['normal'::text, 'heavy'::text, 'minimal'::text, 'stopped'::text, 'foul_smelling'::text])),
  bleeding_color TEXT,
  pad_changes_per_day INTEGER,
  pain_level INTEGER CHECK (pain_level >= 0 AND pain_level <= 10),
  pain_location JSONB DEFAULT '[]'::jsonb,
  temperature_celsius NUMERIC,
  has_fever BOOLEAN DEFAULT false,
  wound_type TEXT CHECK (wound_type = ANY (ARRAY['none'::text, 'cesarean'::text, 'episiotomy'::text, 'tear'::text])),
  wound_healing TEXT CHECK (wound_healing = ANY (ARRAY['normal'::text, 'infection'::text, 'dehiscence'::text, 'delayed'::text])),
  wound_signs JSONB DEFAULT '[]'::jsonb,
  breastfeeding_status TEXT CHECK (breastfeeding_status = ANY (ARRAY['exclusive'::text, 'mixed'::text, 'formula_only'::text, 'not_initiated'::text, 'stopped'::text])),
  breastfeeding_frequency_per_day INTEGER,
  breastfeeding_issues JSONB DEFAULT '[]'::jsonb,
  infant_latching_well BOOLEAN,
  milk_supply TEXT CHECK (milk_supply = ANY (ARRAY['adequate'::text, 'insufficient'::text, 'oversupply'::text])),
  mood_score INTEGER CHECK (mood_score >= 0 AND mood_score <= 10),
  has_crying_episodes BOOLEAN,
  sleep_quality TEXT CHECK (sleep_quality = ANY (ARRAY['good'::text, 'fair'::text, 'poor'::text, 'severe_insomnia'::text])),
  has_anxiety BOOLEAN,
  has_negative_thoughts BOOLEAN,
  depression_risk TEXT CHECK (depression_risk = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
  epds_score INTEGER,
  appetite TEXT CHECK (appetite = ANY (ARRAY['good'::text, 'reduced'::text, 'none'::text])),
  hydration_adequate BOOLEAN DEFAULT true,
  bowel_movement_regular BOOLEAN DEFAULT true,
  urination_issues JSONB DEFAULT '[]'::jsonb,
  risk_level TEXT NOT NULL CHECK (risk_level = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text, 'critical'::text])),
  risk_factors JSONB DEFAULT '[]'::jsonb,
  immediate_action_needed BOOLEAN DEFAULT false,
  notes TEXT,
  recorded_by UUID REFERENCES user_profiles(id),
  referral_made BOOLEAN DEFAULT false,
  referral_facility TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for postnatal_checkins
CREATE INDEX IF NOT EXISTS idx_postnatal_checkins_mother 
    ON postnatal_checkins(mother_id, checkin_date DESC);

-- Enable RLS for postnatal_checkins
ALTER TABLE postnatal_checkins ENABLE ROW LEVEL SECURITY;

-- Create policies for postnatal_checkins
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_checkins' AND policyname = 'postnatal_checkins_select_policy') THEN
        CREATE POLICY postnatal_checkins_select_policy ON postnatal_checkins FOR SELECT USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_checkins' AND policyname = 'postnatal_checkins_insert_policy') THEN
        CREATE POLICY postnatal_checkins_insert_policy ON postnatal_checkins FOR INSERT WITH CHECK (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_checkins' AND policyname = 'postnatal_checkins_update_policy') THEN
        CREATE POLICY postnatal_checkins_update_policy ON postnatal_checkins FOR UPDATE USING (true);
    END IF;
END $$;


-- Create indexes for postnatal_assessments
CREATE INDEX IF NOT EXISTS idx_postnatal_assessments_mother 
    ON postnatal_assessments(mother_id, assessment_date DESC);


CREATE INDEX IF NOT EXISTS idx_postnatal_assessments_child 
    ON postnatal_assessments(child_id, assessment_date DESC);

CREATE INDEX IF NOT EXISTS idx_postnatal_assessments_type 
    ON postnatal_assessments(assessment_type);

-- Enable RLS
ALTER TABLE postnatal_assessments ENABLE ROW LEVEL SECURITY;

-- Create policies
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_assessments' AND policyname = 'postnatal_assessments_select_policy') THEN
        CREATE POLICY postnatal_assessments_select_policy ON postnatal_assessments FOR SELECT USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_assessments' AND policyname = 'postnatal_assessments_insert_policy') THEN
        CREATE POLICY postnatal_assessments_insert_policy ON postnatal_assessments FOR INSERT WITH CHECK (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'postnatal_assessments' AND policyname = 'postnatal_assessments_update_policy') THEN
        CREATE POLICY postnatal_assessments_update_policy ON postnatal_assessments FOR UPDATE USING (true);
    END IF;
END $$;


-- ==================== ROW LEVEL SECURITY (RLS) ====================
-- Enable RLS on all tables if not already enabled

ALTER TABLE vaccinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE growth_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE feeding_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE child_health_timeline ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (if not exist)
DO $$
BEGIN
    -- Vaccinations policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'vaccinations' AND policyname = 'vaccinations_select_policy') THEN
        CREATE POLICY vaccinations_select_policy ON vaccinations FOR SELECT USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'vaccinations' AND policyname = 'vaccinations_insert_policy') THEN
        CREATE POLICY vaccinations_insert_policy ON vaccinations FOR INSERT WITH CHECK (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'vaccinations' AND policyname = 'vaccinations_update_policy') THEN
        CREATE POLICY vaccinations_update_policy ON vaccinations FOR UPDATE USING (true);
    END IF;
    
    -- Growth records policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'growth_records' AND policyname = 'growth_records_select_policy') THEN
        CREATE POLICY growth_records_select_policy ON growth_records FOR SELECT USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'growth_records' AND policyname = 'growth_records_insert_policy') THEN
        CREATE POLICY growth_records_insert_policy ON growth_records FOR INSERT WITH CHECK (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'growth_records' AND policyname = 'growth_records_update_policy') THEN
        CREATE POLICY growth_records_update_policy ON growth_records FOR UPDATE USING (true);
    END IF;
    
    -- Milestones policies
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'milestones' AND policyname = 'milestones_select_policy') THEN
        CREATE POLICY milestones_select_policy ON milestones FOR SELECT USING (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'milestones' AND policyname = 'milestones_insert_policy') THEN
        CREATE POLICY milestones_insert_policy ON milestones FOR INSERT WITH CHECK (true);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'milestones' AND policyname = 'milestones_update_policy') THEN
        CREATE POLICY milestones_update_policy ON milestones FOR UPDATE USING (true);
    END IF;
END $$;


-- ==================== HELPER FUNCTIONS ====================

-- Function to calculate child age in months
CREATE OR REPLACE FUNCTION calculate_child_age_months(birth_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(NOW(), birth_date)) * 12 + 
           EXTRACT(MONTH FROM AGE(NOW(), birth_date));
END;
$$ LANGUAGE plpgsql;

-- Function to calculate child age in days  
CREATE OR REPLACE FUNCTION calculate_child_age_days(birth_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(DAY FROM (NOW() - birth_date));
END;
$$ LANGUAGE plpgsql;

-- Function to update vaccination status based on due date
CREATE OR REPLACE FUNCTION update_vaccination_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'pending' AND NEW.due_date < CURRENT_DATE THEN
        NEW.status := 'overdue';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating vaccination status
DROP TRIGGER IF EXISTS vaccination_status_trigger ON vaccinations;
CREATE TRIGGER vaccination_status_trigger
    BEFORE INSERT OR UPDATE ON vaccinations
    FOR EACH ROW
    EXECUTE FUNCTION update_vaccination_status();


-- ==================== DEFAULT MILESTONE DATA ====================
-- This creates standard RBSK milestones that can be assigned to children

-- Create a milestones_template table if needed for standard milestones
CREATE TABLE IF NOT EXISTS milestone_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL CHECK (category IN ('gross_motor', 'fine_motor', 'language', 'cognitive', 'social_emotional', 'self_care')),
    milestone_name TEXT NOT NULL,
    expected_age_months INTEGER NOT NULL,
    expected_age_range_start INTEGER,
    expected_age_range_end INTEGER,
    description TEXT,
    warning_signs TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert standard milestones if table is empty
INSERT INTO milestone_templates (category, milestone_name, expected_age_months, expected_age_range_start, expected_age_range_end, description)
SELECT * FROM (VALUES
    ('gross_motor', 'Moves arms and legs', 0, 0, 1, 'Shows active limb movements'),
    ('gross_motor', 'Lifts head briefly', 2, 1, 3, 'When lying on tummy'),
    ('gross_motor', 'Holds head steady', 4, 3, 5, 'Good head control when supported'),
    ('gross_motor', 'Sits with support', 6, 5, 7, 'Sits when propped'),
    ('gross_motor', 'Sits without support', 9, 7, 10, 'Sits independently'),
    ('gross_motor', 'Crawls', 9, 7, 12, 'Moves on hands and knees'),
    ('gross_motor', 'Stands alone', 12, 10, 14, 'Stands without support briefly'),
    ('gross_motor', 'Walks with support', 12, 10, 14, 'Cruises along furniture'),
    ('gross_motor', 'Walks independently', 18, 12, 18, 'Walks without support'),
    ('gross_motor', 'Runs', 24, 18, 30, 'Runs with coordination'),
    ('fine_motor', 'Reaches for objects', 4, 3, 5, 'Attempts to grasp toys'),
    ('fine_motor', 'Transfers objects', 6, 5, 8, 'Passes toy from hand to hand'),
    ('fine_motor', 'Pincer grasp developing', 9, 8, 12, 'Picks small objects with fingers'),
    ('fine_motor', 'Scribbles', 18, 15, 24, 'Holds crayon and scribbles'),
    ('language', 'Coos and babbles', 4, 2, 6, 'Makes vowel sounds'),
    ('language', 'Responds to name', 6, 5, 9, 'Turns when name is called'),
    ('language', 'Says mama/dada', 9, 8, 12, 'Non-specific babbling'),
    ('language', '1-2 words', 12, 10, 15, 'Says specific words like mama/dada'),
    ('language', '15-20 words', 18, 15, 24, 'Vocabulary expanding'),
    ('language', '2-word sentences', 24, 18, 30, 'Combines words'),
    ('cognitive', 'Object permanence', 12, 9, 15, 'Looks for hidden objects'),
    ('cognitive', 'Follows 2-step commands', 24, 18, 30, 'Understands instructions'),
    ('social_emotional', 'Looks at faces', 0, 0, 2, 'Focuses briefly on caregivers face'),
    ('social_emotional', 'Social smile', 2, 1, 3, 'Smiles in response to caregiver'),
    ('social_emotional', 'Laughs', 4, 3, 5, 'Laughs out loud'),
    ('social_emotional', 'Stranger anxiety', 6, 5, 9, 'Shows preference for familiar faces'),
    ('social_emotional', 'Parallel play', 18, 15, 24, 'Plays alongside other children')
) AS v(category, milestone_name, expected_age_months, expected_age_range_start, expected_age_range_end, description)
WHERE NOT EXISTS (SELECT 1 FROM milestone_templates LIMIT 1);


-- ==================== VACCINATION SCHEDULE TEMPLATES ====================
-- IAP 2023 Vaccination Schedule Reference

CREATE TABLE IF NOT EXISTS vaccination_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vaccine_name TEXT NOT NULL UNIQUE,
    vaccine_category TEXT CHECK (vaccine_category IN ('birth', 'primary', 'booster', 'catch_up', 'optional')),
    recommended_age_days INTEGER NOT NULL,
    dose_number INTEGER,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert IAP 2023 schedule
INSERT INTO vaccination_templates (vaccine_name, vaccine_category, recommended_age_days, dose_number, description, is_mandatory)
SELECT * FROM (VALUES
    ('BCG', 'birth', 0, 1, 'Tuberculosis prevention', true),
    ('OPV-0', 'birth', 0, 1, 'Oral Polio Vaccine birth dose', true),
    ('Hepatitis B-1', 'birth', 0, 1, 'Hepatitis B birth dose', true),
    ('OPV-1 + IPV-1', 'primary', 42, 1, '6 weeks - Polio vaccines', true),
    ('Pentavalent-1', 'primary', 42, 1, '6 weeks - DPT + Hep B + Hib', true),
    ('Rotavirus-1', 'primary', 42, 1, '6 weeks - Rotavirus', true),
    ('PCV-1', 'primary', 42, 1, '6 weeks - Pneumococcal', true),
    ('OPV-2 + IPV-2', 'primary', 70, 2, '10 weeks - Polio vaccines', true),
    ('Pentavalent-2', 'primary', 70, 2, '10 weeks - DPT + Hep B + Hib', true),
    ('Rotavirus-2', 'primary', 70, 2, '10 weeks - Rotavirus', true),
    ('OPV-3 + IPV-3', 'primary', 98, 3, '14 weeks - Polio vaccines', true),
    ('Pentavalent-3', 'primary', 98, 3, '14 weeks - DPT + Hep B + Hib', true),
    ('Rotavirus-3', 'primary', 98, 3, '14 weeks - Rotavirus', true),
    ('PCV-2', 'primary', 98, 2, '14 weeks - Pneumococcal booster', true),
    ('Measles-1 (MR/MMR)', 'primary', 270, 1, '9 months - Measles/Rubella', true),
    ('Vitamin A-1', 'primary', 270, 1, '9 months - Vitamin A supplement', true),
    ('PCV Booster', 'booster', 365, 1, '12 months - Pneumococcal booster', true),
    ('Measles-2 (MMR)', 'booster', 450, 2, '15 months - MMR booster', true),
    ('DPT Booster-1', 'booster', 540, 1, '18 months - DPT booster', true),
    ('DPT Booster-2', 'booster', 1460, 2, '4-5 years - DPT booster', true),
    ('Typhoid', 'optional', 730, 1, '2 years - Typhoid conjugate', false),
    ('Hepatitis A', 'optional', 365, 1, '12 months - Hepatitis A', false)
) AS v(vaccine_name, vaccine_category, recommended_age_days, dose_number, description, is_mandatory)
WHERE NOT EXISTS (SELECT 1 FROM vaccination_templates LIMIT 1);


-- ==================== NOTIFICATION LOG FOR SANTANRAKSHA ====================

CREATE TABLE IF NOT EXISTS child_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    mother_id UUID REFERENCES mothers(id),
    notification_type TEXT NOT NULL CHECK (notification_type IN ('vaccination_due', 'vaccination_overdue', 'growth_alert', 'milestone_delay', 'health_check', 'appointment')),
    message TEXT NOT NULL,
    language TEXT DEFAULT 'hindi',
    sent_via TEXT CHECK (sent_via IN ('telegram', 'sms', 'whatsapp', 'push')),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivery_status TEXT DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed')),
    read_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_child_notifications_child 
    ON child_notifications(child_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_child_notifications_mother 
    ON child_notifications(mother_id, created_at DESC);


-- ==================== GRANT PERMISSIONS ====================
-- Grant permissions to authenticated and service role

GRANT ALL ON vaccinations TO authenticated, service_role;
GRANT ALL ON growth_records TO authenticated, service_role;
GRANT ALL ON milestones TO authenticated, service_role;
GRANT ALL ON feeding_records TO authenticated, service_role;
GRANT ALL ON child_health_timeline TO authenticated, service_role;
GRANT ALL ON milestone_templates TO authenticated, service_role;
GRANT ALL ON vaccination_templates TO authenticated, service_role;
GRANT ALL ON child_notifications TO authenticated, service_role;
GRANT ALL ON postnatal_assessments TO authenticated, service_role;
GRANT ALL ON postnatal_checkins TO authenticated, service_role;

-- Grant sequence usage
-- Grant sequence usage
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;


-- ==================== NEW COLUMNS FOR DOCTOR ASSESSMENTS ====================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'postnatal_assessments' AND column_name = 'nutrition_advice') THEN
        ALTER TABLE postnatal_assessments ADD COLUMN nutrition_advice TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'postnatal_assessments' AND column_name = 'medications') THEN
        ALTER TABLE postnatal_assessments ADD COLUMN medications TEXT;
    END IF;
END $$;


-- ============================================================
-- VERIFICATION QUERIES (Run these to verify data structure)
-- ============================================================

-- Uncomment and run these to verify your schema:

-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'vaccinations' 
-- ORDER BY ordinal_position;

-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'growth_records' 
-- ORDER BY ordinal_position;

-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'milestones' 
-- ORDER BY ordinal_position;

-- Check RLS policies
-- SELECT tablename, policyname, permissive, roles, cmd, qual
-- FROM pg_policies
-- WHERE tablename IN ('vaccinations', 'growth_records', 'milestones');

-- ==================== FIX EXISTING TABLES ====================
-- If table exists with UUID column, change it to TEXT
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'postnatal_assessments' AND column_name = 'assessor_id' AND data_type = 'uuid') THEN
        ALTER TABLE postnatal_assessments ALTER COLUMN assessor_id TYPE TEXT USING assessor_id::text;
    END IF;
END $$;

SELECT 'SantanRaksha Migration v2 completed successfully!' AS status;
