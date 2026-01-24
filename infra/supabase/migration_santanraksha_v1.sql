-- ============================================================
-- SantanRaksha Database Migration v1.0
-- Extends MatruRaksha schema for postnatal & child health monitoring
-- Aligned with: NHM SUMAN, RBSK, IAP Immunization Schedule 2023, WHO standards
-- ============================================================

-- ========== CHILDREN TABLE ==========
-- Core table for child registration and profile
CREATE TABLE IF NOT EXISTS public.children (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mother_id UUID NOT NULL REFERENCES public.mothers(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  birth_date DATE NOT NULL,
  birth_weight_kg DECIMAL(4,2), -- e.g., 2.95 kg
  birth_length_cm DECIMAL(4,1), -- e.g., 48.5 cm
  birth_head_circumference_cm DECIMAL(4,1),
  delivery_type TEXT CHECK (delivery_type IN ('normal', 'cesarean', 'assisted', 'forceps', 'vacuum')),
  gestational_age_weeks INTEGER CHECK (gestational_age_weeks BETWEEN 20 AND 45), -- Premature/term tracking
  apgar_score_1min INTEGER CHECK (apgar_score_1min BETWEEN 0 AND 10),
  apgar_score_5min INTEGER CHECK (apgar_score_5min BETWEEN 0 AND 10),
  birth_complications JSONB DEFAULT '[]'::jsonb, -- ["jaundice", "respiratory_distress"]
  blood_group TEXT,
  photo_url TEXT, -- Supabase Storage URL
  is_active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'::jsonb, -- Extensible field for additional data
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.children IS 'Child profiles linked to mothers for comprehensive health tracking';
COMMENT ON COLUMN public.children.gestational_age_weeks IS 'Actual weeks at birth - critical for premature baby monitoring';
COMMENT ON COLUMN public.children.apgar_score_1min IS 'APGAR score at 1 minute - WHO newborn assessment standard';

-- ========== VACCINATIONS TABLE ==========
-- Comprehensive vaccination tracking per IAP 2023 schedule
CREATE TABLE IF NOT EXISTS public.vaccinations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  vaccine_name TEXT NOT NULL, -- 'BCG', 'OPV-0', 'OPV-1', 'Pentavalent-1', 'Rotavirus-1', 'PCV-1', etc.
  vaccine_category TEXT CHECK (vaccine_category IN ('birth', 'primary', 'booster', 'catch_up', 'optional')),
  recommended_age_days INTEGER NOT NULL, -- Days from birth (e.g., BCG = 0, OPV-1 = 42)
  due_date DATE NOT NULL,
  administered_date DATE,
  administered_by TEXT, -- ASHA worker name or clinic
  administered_at_facility TEXT, -- PHC/CHC name
  batch_number TEXT, -- Vaccine batch tracking for recall management
  manufacturer TEXT,
  site TEXT, -- Injection site: 'left_thigh', 'right_arm', 'oral', etc.
  dose_number INTEGER, -- For multi-dose vaccines (1, 2, 3)
  adverse_reaction TEXT, -- Free text or JSONB
  adverse_reaction_severity TEXT CHECK (adverse_reaction_severity IN ('none', 'mild', 'moderate', 'severe')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'overdue', 'skipped', 'contraindicated')),
  skip_reason TEXT, -- Required if status = 'skipped' or 'contraindicated'
  reminder_sent_at TIMESTAMPTZ,
  reminder_count INTEGER DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.vaccinations IS 'IAP 2023 immunization schedule tracking with batch traceability';
COMMENT ON COLUMN public.vaccinations.recommended_age_days IS 'Standard age in days per IAP schedule for automated scheduling';

-- ========== GROWTH RECORDS TABLE ==========
-- WHO Child Growth Standards monitoring
CREATE TABLE IF NOT EXISTS public.growth_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  measurement_date DATE NOT NULL,
  age_months INTEGER NOT NULL, -- Calculated from birth_date
  age_days INTEGER NOT NULL, -- For precise z-score calculation
  weight_kg DECIMAL(5,3), -- e.g., 8.450 kg
  height_cm DECIMAL(5,2), -- e.g., 72.50 cm
  head_circumference_cm DECIMAL(4,1), -- Critical for 0-24 months
  muac_cm DECIMAL(3,1), -- Mid-Upper Arm Circumference - malnutrition screening
  
  -- WHO z-scores (calculated using WHO LMS parameters)
  weight_for_age_z_score DECIMAL(5,3),
  height_for_age_z_score DECIMAL(5,3),
  weight_for_height_z_score DECIMAL(5,3),
  bmi_for_age_z_score DECIMAL(5,3),
  head_circumference_z_score DECIMAL(5,3),
  
  -- Growth status classification (RBSK standards)
  growth_status TEXT CHECK (growth_status IN (
    'normal', 
    'at_risk', 
    'moderate_acute_malnutrition', -- MAM: -3 SD < WHZ < -2 SD
    'severe_acute_malnutrition',   -- SAM: WHZ < -3 SD
    'stunted',                      -- HAZ < -2 SD
    'severely_stunted',             -- HAZ < -3 SD
    'overweight',                   -- WHZ > +2 SD
    'obese'                         -- WHZ > +3 SD
  )),
  
  measured_by UUID REFERENCES public.user_profiles(id), -- ASHA worker or doctor
  measurement_location TEXT, -- 'home_visit', 'anganwadi', 'phc', 'chc'
  notes TEXT,
  alert_generated BOOLEAN DEFAULT FALSE, -- True if flagged for ASHA/doctor review
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.growth_records IS 'WHO growth standards monitoring with automated z-score calculation';
COMMENT ON COLUMN public.growth_records.muac_cm IS 'MUAC < 11.5cm indicates SAM per WHO emergency guidelines';

-- ========== MILESTONES TABLE ==========
-- RBSK developmental screening checklist
CREATE TABLE IF NOT EXISTS public.milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN (
    'gross_motor',      -- Sitting, walking, running
    'fine_motor',       -- Grasping, drawing
    'language',         -- Babbling, first words, sentences
    'cognitive',        -- Problem solving, memory
    'social_emotional', -- Smiling, stranger anxiety, play
    'self_care'         -- Feeding, toilet training
  )),
  milestone_name TEXT NOT NULL, -- 'Sits without support', 'Says first word', etc.
  milestone_code TEXT, -- RBSK standard codes if applicable
  expected_age_months INTEGER NOT NULL, -- WHO/RBSK developmental standards
  expected_age_range_start INTEGER, -- Acceptable range start (e.g., 6 months)
  expected_age_range_end INTEGER,   -- Acceptable range end (e.g., 9 months)
  
  achieved_date DATE,
  achieved_age_months INTEGER,
  achieved_age_days INTEGER,
  is_achieved BOOLEAN DEFAULT FALSE,
  is_delayed BOOLEAN DEFAULT FALSE, -- True if achieved_age > expected_age_range_end
  delay_in_months INTEGER, -- Calculated delay
  
  observed_by UUID REFERENCES public.user_profiles(id),
  observation_method TEXT CHECK (observation_method IN ('parent_report', 'direct_observation', 'clinical_assessment')),
  notes TEXT,
  referral_needed BOOLEAN DEFAULT FALSE, -- Flag for specialist referral
  referral_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.milestones IS 'RBSK developmental milestone tracking - 4Ds screening (Defects, Diseases, Deficiencies, Development delays)';

-- ========== POSTNATAL CHECKINS TABLE ==========
-- Mother's postnatal recovery monitoring (NHM SUMAN 6-week protocol)
CREATE TABLE IF NOT EXISTS public.postnatal_checkins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mother_id UUID NOT NULL REFERENCES public.mothers(id) ON DELETE CASCADE,
  checkin_date DATE NOT NULL,
  days_postpartum INTEGER NOT NULL,
  
  -- Physical recovery indicators
  bleeding_status TEXT CHECK (bleeding_status IN ('normal', 'heavy', 'minimal', 'stopped', 'foul_smelling')),
  bleeding_color TEXT, -- 'red', 'brown', 'pink'
  pad_changes_per_day INTEGER,
  pain_level INTEGER CHECK (pain_level BETWEEN 0 AND 10),
  pain_location JSONB DEFAULT '[]'::jsonb, -- ["abdomen", "perineum", "cesarean_scar"]
  temperature_celsius DECIMAL(3,1),
  has_fever BOOLEAN DEFAULT FALSE,
  
  -- Wound healing (cesarean/episiotomy)
  wound_type TEXT CHECK (wound_type IN ('none', 'cesarean', 'episiotomy', 'tear')),
  wound_healing TEXT CHECK (wound_healing IN ('normal', 'infection', 'dehiscence', 'delayed')),
  wound_signs JSONB DEFAULT '[]'::jsonb, -- ["redness", "discharge", "swelling", "pain"]
  
  -- Breastfeeding assessment
  breastfeeding_status TEXT CHECK (breastfeeding_status IN (
    'exclusive',        -- Only breast milk
    'mixed',           -- Breast milk + formula
    'formula_only',
    'not_initiated',
    'stopped'
  )),
  breastfeeding_frequency_per_day INTEGER,
  breastfeeding_issues JSONB DEFAULT '[]'::jsonb, -- [{"issue": "cracked_nipples", "severity": "moderate"}]
  infant_latching_well BOOLEAN,
  milk_supply TEXT CHECK (milk_supply IN ('adequate', 'insufficient', 'oversupply')),
  
  -- Mental health screening (EPDS - Edinburgh Postnatal Depression Scale)
  mood_score INTEGER CHECK (mood_score BETWEEN 0 AND 10), -- 0=worst, 10=best (inverse of EPDS)
  has_crying_episodes BOOLEAN,
  sleep_quality TEXT CHECK (sleep_quality IN ('good', 'fair', 'poor', 'severe_insomnia')),
  has_anxiety BOOLEAN,
  has_negative_thoughts BOOLEAN,
  depression_risk TEXT CHECK (depression_risk IN ('low', 'medium', 'high', 'critical')),
  epds_score INTEGER, -- Full EPDS questionnaire score (0-30, >13 = likely depression)
  
  -- General health
  appetite TEXT CHECK (appetite IN ('good', 'reduced', 'none')),
  hydration_adequate BOOLEAN DEFAULT TRUE,
  bowel_movement_regular BOOLEAN DEFAULT TRUE,
  urination_issues JSONB DEFAULT '[]'::jsonb, -- ["burning", "frequency", "incontinence"]
  
  -- Risk assessment
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
  risk_factors JSONB DEFAULT '[]'::jsonb,
  immediate_action_needed BOOLEAN DEFAULT FALSE,
  
  notes TEXT,
  recorded_by UUID REFERENCES public.user_profiles(id), -- ASHA worker or self-reported
  referral_made BOOLEAN DEFAULT FALSE,
  referral_facility TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.postnatal_checkins IS 'NHM SUMAN postnatal care protocol - 6 critical checkpoints (48hr, 3d, 7d, 14d, 28d, 42d)';
COMMENT ON COLUMN public.postnatal_checkins.epds_score IS 'Edinburgh Postnatal Depression Scale - WHO recommended screening tool';

-- ========== CHILD HEALTH TIMELINE TABLE ==========
-- Comprehensive health events tracking for children
CREATE TABLE IF NOT EXISTS public.child_health_timeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  event_date DATE NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'illness',           -- Fever, diarrhea, respiratory infection
    'hospitalization',   -- Admission details
    'emergency_visit',   -- A&E visits
    'routine_checkup',   -- Well-baby visits
    'vaccination',       -- Link to vaccinations table
    'growth_measurement',-- Link to growth_records table
    'milestone_achieved',-- Link to milestones table
    'injury',           -- Accidents, falls
    'allergy_identified',
    'medication_started',
    'feeding_change',   -- Introduction of solids, weaning
    'other'
  )),
  
  -- Illness tracking (IMNCI - Integrated Management of Neonatal and Childhood Illness)
  symptoms JSONB DEFAULT '[]'::jsonb, -- ["fever", "cough", "diarrhea", "vomiting"]
  temperature_celsius DECIMAL(3,1),
  respiratory_rate INTEGER, -- Critical for IMNCI pneumonia classification
  danger_signs JSONB DEFAULT '[]'::jsonb, -- ["lethargic", "unable_to_drink", "convulsions", "chest_indrawing"]
  diagnosis TEXT,
  treatment TEXT,
  medication_prescribed JSONB DEFAULT '[]'::jsonb,
  
  -- Outcome tracking
  outcome TEXT CHECK (outcome IN ('recovered', 'improving', 'referred', 'hospitalized', 'died', 'ongoing')),
  follow_up_date DATE,
  
  -- Provider details
  attended_by UUID REFERENCES public.user_profiles(id),
  facility TEXT,
  
  summary TEXT,
  event_data JSONB DEFAULT '{}'::jsonb, -- Extensible field for event-specific data
  alert_generated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.child_health_timeline IS 'Comprehensive health event tracking using IMNCI (Integrated Management of Neonatal and Childhood Illness) guidelines';

-- ========== FEEDING RECORDS TABLE ==========
-- Infant and young child feeding practices (6-24 months critical window)
CREATE TABLE IF NOT EXISTS public.feeding_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id UUID NOT NULL REFERENCES public.children(id) ON DELETE CASCADE,
  record_date DATE NOT NULL,
  age_months INTEGER NOT NULL,
  
  -- Breastfeeding status (WHO IYCF indicators)
  is_breastfeeding BOOLEAN,
  exclusive_breastfeeding BOOLEAN, -- <6 months only
  breastfeeding_frequency_per_day INTEGER,
  
  -- Complementary feeding (6+ months)
  complementary_feeding_started BOOLEAN DEFAULT FALSE,
  complementary_feeding_start_age_months INTEGER,
  meal_frequency_per_day INTEGER, -- WHO recommends 2-3 times at 6-8m, 3-4 times at 9-24m
  food_groups_consumed JSONB DEFAULT '[]'::jsonb, -- ["grains", "legumes", "dairy", "eggs", "meat", "fruits", "vegetables"]
  minimum_dietary_diversity_met BOOLEAN, -- >=4 food groups per WHO
  
  -- Feeding practices
  feeding_method TEXT CHECK (feeding_method IN ('spoon', 'bottle', 'self_feeding', 'mixed')),
  appetite TEXT CHECK (appetite IN ('good', 'fair', 'poor', 'refuses')),
  feeding_difficulties JSONB DEFAULT '[]'::jsonb, -- ["choking", "gagging", "refusal", "allergies"]
  
  -- Specific foods introduced (allergy tracking)
  new_foods_introduced JSONB DEFAULT '[]'::jsonb,
  allergic_reactions JSONB DEFAULT '[]'::jsonb,
  
  notes TEXT,
  recorded_by UUID REFERENCES public.user_profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.feeding_records IS 'WHO Infant and Young Child Feeding (IYCF) practices monitoring - critical for growth';

-- ========== INDEXES FOR PERFORMANCE ==========

-- Children table indexes
CREATE INDEX IF NOT EXISTS idx_children_mother_id ON public.children(mother_id);
CREATE INDEX IF NOT EXISTS idx_children_birth_date ON public.children(birth_date DESC);
CREATE INDEX IF NOT EXISTS idx_children_is_active ON public.children(is_active) WHERE is_active = TRUE;

-- Vaccinations table indexes
CREATE INDEX IF NOT EXISTS idx_vaccinations_child_id ON public.vaccinations(child_id);
CREATE INDEX IF NOT EXISTS idx_vaccinations_status ON public.vaccinations(status);
CREATE INDEX IF NOT EXISTS idx_vaccinations_due_date ON public.vaccinations(due_date);
CREATE INDEX IF NOT EXISTS idx_vaccinations_overdue ON public.vaccinations(due_date, status) 
  WHERE status = 'pending' OR status = 'overdue'; -- Fast overdue vaccine queries

-- Growth records table indexes
CREATE INDEX IF NOT EXISTS idx_growth_records_child_id_date ON public.growth_records(child_id, measurement_date DESC);
CREATE INDEX IF NOT EXISTS idx_growth_records_alert ON public.growth_records(alert_generated, growth_status) 
  WHERE alert_generated = TRUE; -- Fast alert queries
CREATE INDEX IF NOT EXISTS idx_growth_records_child_latest ON public.growth_records(child_id, measurement_date DESC);

-- Milestones table indexes
CREATE INDEX IF NOT EXISTS idx_milestones_child_id ON public.milestones(child_id);
CREATE INDEX IF NOT EXISTS idx_milestones_delayed ON public.milestones(is_delayed) WHERE is_delayed = TRUE;
CREATE INDEX IF NOT EXISTS idx_milestones_referral ON public.milestones(referral_needed) WHERE referral_needed = TRUE;

-- Postnatal checkins table indexes
CREATE INDEX IF NOT EXISTS idx_postnatal_checkins_mother_id_date ON public.postnatal_checkins(mother_id, checkin_date DESC);
CREATE INDEX IF NOT EXISTS idx_postnatal_checkins_risk ON public.postnatal_checkins(risk_level, immediate_action_needed);
CREATE INDEX IF NOT EXISTS idx_postnatal_checkins_high_risk ON public.postnatal_checkins(mother_id, risk_level) 
  WHERE risk_level IN ('high', 'critical');

-- Child health timeline indexes
CREATE INDEX IF NOT EXISTS idx_child_health_timeline_child_date ON public.child_health_timeline(child_id, event_date DESC);
CREATE INDEX IF NOT EXISTS idx_child_health_timeline_event_type ON public.child_health_timeline(event_type);
CREATE INDEX IF NOT EXISTS idx_child_health_timeline_alerts ON public.child_health_timeline(alert_generated) WHERE alert_generated = TRUE;

-- Feeding records indexes
CREATE INDEX IF NOT EXISTS idx_feeding_records_child_date ON public.feeding_records(child_id, record_date DESC);

-- ========== UPDATED_AT TRIGGERS ==========

-- Trigger for children table
DROP TRIGGER IF EXISTS update_children_updated_at ON public.children;
CREATE TRIGGER update_children_updated_at
  BEFORE UPDATE ON public.children
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for vaccinations table
DROP TRIGGER IF EXISTS update_vaccinations_updated_at ON public.vaccinations;
CREATE TRIGGER update_vaccinations_updated_at
  BEFORE UPDATE ON public.vaccinations
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for growth_records table
DROP TRIGGER IF EXISTS update_growth_records_updated_at ON public.growth_records;
CREATE TRIGGER update_growth_records_updated_at
  BEFORE UPDATE ON public.growth_records
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for milestones table
DROP TRIGGER IF EXISTS update_milestones_updated_at ON public.milestones;
CREATE TRIGGER update_milestones_updated_at
  BEFORE UPDATE ON public.milestones
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for postnatal_checkins table
DROP TRIGGER IF EXISTS update_postnatal_checkins_updated_at ON public.postnatal_checkins;
CREATE TRIGGER update_postnatal_checkins_updated_at
  BEFORE UPDATE ON public.postnatal_checkins
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for child_health_timeline table
DROP TRIGGER IF EXISTS update_child_health_timeline_updated_at ON public.child_health_timeline;
CREATE TRIGGER update_child_health_timeline_updated_at
  BEFORE UPDATE ON public.child_health_timeline
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ========== AUTOMATED FUNCTIONS ==========

-- Function to auto-update vaccination status to 'overdue'
CREATE OR REPLACE FUNCTION public.update_overdue_vaccinations()
RETURNS void AS $$
BEGIN
  UPDATE public.vaccinations
  SET status = 'overdue',
      updated_at = NOW()
  WHERE status = 'pending'
    AND due_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.update_overdue_vaccinations IS 'Scheduled function to flag overdue vaccinations - run daily via cron';

-- Function to calculate child age in months and days
CREATE OR REPLACE FUNCTION public.calculate_child_age(birth_date DATE, reference_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE(age_months INTEGER, age_days INTEGER) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    EXTRACT(YEAR FROM AGE(reference_date, birth_date))::INTEGER * 12 + 
    EXTRACT(MONTH FROM AGE(reference_date, birth_date))::INTEGER AS age_months,
    (reference_date - birth_date)::INTEGER AS age_days;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION public.calculate_child_age IS 'Utility function to calculate precise child age for z-score calculations';

-- Function to generate vaccination schedule for a new child
CREATE OR REPLACE FUNCTION public.generate_vaccination_schedule(p_child_id UUID, p_birth_date DATE)
RETURNS void AS $$
DECLARE
  v_vaccine RECORD;
BEGIN
  -- IAP 2023 Immunization Schedule
  -- Note: This is a basic implementation. Full schedule should be maintained in a vaccines_master table
  
  -- Birth vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date)
  VALUES 
    (p_child_id, 'BCG', 'birth', 0, p_birth_date),
    (p_child_id, 'OPV-0', 'birth', 0, p_birth_date),
    (p_child_id, 'Hepatitis B-1', 'birth', 0, p_birth_date);
  
  -- 6 weeks vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date, dose_number)
  VALUES 
    (p_child_id, 'OPV-1', 'primary', 42, p_birth_date + 42, 1),
    (p_child_id, 'Pentavalent-1', 'primary', 42, p_birth_date + 42, 1),
    (p_child_id, 'Rotavirus-1', 'primary', 42, p_birth_date + 42, 1),
    (p_child_id, 'PCV-1', 'primary', 42, p_birth_date + 42, 1),
    (p_child_id, 'IPV-1', 'primary', 42, p_birth_date + 42, 1);
  
  -- 10 weeks vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date, dose_number)
  VALUES 
    (p_child_id, 'OPV-2', 'primary', 70, p_birth_date + 70, 2),
    (p_child_id, 'Pentavalent-2', 'primary', 70, p_birth_date + 70, 2),
    (p_child_id, 'Rotavirus-2', 'primary', 70, p_birth_date + 70, 2),
    (p_child_id, 'PCV-2', 'primary', 70, p_birth_date + 70, 2);
  
  -- 14 weeks vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date, dose_number)
  VALUES 
    (p_child_id, 'OPV-3', 'primary', 98, p_birth_date + 98, 3),
    (p_child_id, 'Pentavalent-3', 'primary', 98, p_birth_date + 98, 3),
    (p_child_id, 'Rotavirus-3', 'primary', 98, p_birth_date + 98, 3),
    (p_child_id, 'PCV-3', 'primary', 98, p_birth_date + 98, 3),
    (p_child_id, 'IPV-2', 'primary', 98, p_birth_date + 98, 2);
  
  -- 9 months vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date)
  VALUES 
    (p_child_id, 'MR-1', 'primary', 270, p_birth_date + 270),
    (p_child_id, 'JE-1', 'primary', 270, p_birth_date + 270);
  
  -- 12 months vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date)
  VALUES 
    (p_child_id, 'Hepatitis A-1', 'optional', 365, p_birth_date + 365);
  
  -- 16-18 months vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date, dose_number)
  VALUES 
    (p_child_id, 'Pentavalent Booster', 'booster', 510, p_birth_date + 510, 4),
    (p_child_id, 'OPV Booster', 'booster', 510, p_birth_date + 510, 4),
    (p_child_id, 'MR-2', 'booster', 510, p_birth_date + 510, 2),
    (p_child_id, 'JE-2', 'booster', 510, p_birth_date + 510, 2);
  
  -- 2 years vaccines
  INSERT INTO public.vaccinations (child_id, vaccine_name, vaccine_category, recommended_age_days, due_date)
  VALUES 
    (p_child_id, 'Typhoid Conjugate Vaccine', 'optional', 730, p_birth_date + 730);

  RAISE NOTICE 'Vaccination schedule generated for child %', p_child_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.generate_vaccination_schedule IS 'Auto-generates IAP 2023 vaccination schedule for newborns';

-- ========== ROW LEVEL SECURITY (RLS) POLICIES ==========

-- Enable RLS on new tables
ALTER TABLE public.children ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vaccinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.growth_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.postnatal_checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.child_health_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feeding_records ENABLE ROW LEVEL SECURITY;

-- Policies for children table
CREATE POLICY "Admins can manage all children"
  ON public.children FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

CREATE POLICY "Doctors can view children in their area"
  ON public.children FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles up
      JOIN public.mothers m ON m.doctor_id IN (
        SELECT id FROM public.doctors WHERE user_profile_id = up.id
      )
      WHERE up.id = auth.uid() 
        AND up.role = 'DOCTOR'
        AND m.id = children.mother_id
    )
  );

CREATE POLICY "ASHA workers can view and update children in their area"
  ON public.children FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles up
      JOIN public.mothers m ON m.asha_worker_id IN (
        SELECT id FROM public.asha_workers WHERE user_profile_id = up.id
      )
      WHERE up.id = auth.uid() 
        AND up.role = 'ASHA_WORKER'
        AND m.id = children.mother_id
    )
  );

-- Policies for vaccinations (same access pattern as children)
CREATE POLICY "Admins can manage all vaccinations"
  ON public.vaccinations FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

CREATE POLICY "Healthcare workers can manage vaccinations"
  ON public.vaccinations FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles up
      JOIN public.children c ON c.id = vaccinations.child_id
      JOIN public.mothers m ON m.id = c.mother_id
      WHERE up.id = auth.uid() 
        AND up.role IN ('DOCTOR', 'ASHA_WORKER')
        AND (
          m.doctor_id IN (SELECT id FROM public.doctors WHERE user_profile_id = up.id)
          OR m.asha_worker_id IN (SELECT id FROM public.asha_workers WHERE user_profile_id = up.id)
        )
    )
  );

-- Similar RLS policies for other tables (growth_records, milestones, etc.)
CREATE POLICY "Admins can manage all growth records"
  ON public.growth_records FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'ADMIN'
    )
  );

CREATE POLICY "Healthcare workers can manage growth records"
  ON public.growth_records FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles up
      JOIN public.children c ON c.id = growth_records.child_id
      JOIN public.mothers m ON m.id = c.mother_id
      WHERE up.id = auth.uid() 
        AND up.role IN ('DOCTOR', 'ASHA_WORKER')
    )
  );

-- Postnatal checkins policies
CREATE POLICY "Healthcare workers can manage postnatal checkins"
  ON public.postnatal_checkins FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles up
      JOIN public.mothers m ON m.id = postnatal_checkins.mother_id
      WHERE up.id = auth.uid() 
        AND (
          up.role = 'ADMIN'
          OR (up.role = 'DOCTOR' AND m.doctor_id IN (SELECT id FROM public.doctors WHERE user_profile_id = up.id))
          OR (up.role = 'ASHA_WORKER' AND m.asha_worker_id IN (SELECT id FROM public.asha_workers WHERE user_profile_id = up.id))
        )
    )
  );

-- ========== REALTIME SUBSCRIPTIONS ==========

-- Enable realtime for SantanRaksha tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.children;
ALTER PUBLICATION supabase_realtime ADD TABLE public.vaccinations;
ALTER PUBLICATION supabase_realtime ADD TABLE public.growth_records;
ALTER PUBLICATION supabase_realtime ADD TABLE public.postnatal_checkins;
ALTER PUBLICATION supabase_realtime ADD TABLE public.child_health_timeline;

-- ========== MIGRATION COMPLETE ==========
-- Run this script using: psql -d <database_name> -f migration_santanraksha_v1.sql
-- Or via Supabase CLI: supabase db push

COMMENT ON SCHEMA public IS 'SantanRaksha v1.0 - Comprehensive maternal-child health monitoring system';
