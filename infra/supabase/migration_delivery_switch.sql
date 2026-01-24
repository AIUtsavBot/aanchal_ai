-- ============================================================
-- Delivery Switch Migration - Auto-transition from MatruRaksha to SantanRaksha
-- ============================================================

-- Add delivery tracking fields to mothers table
ALTER TABLE public.mothers 
ADD COLUMN IF NOT EXISTS delivery_status TEXT DEFAULT 'pregnant' CHECK (delivery_status IN ('pregnant', 'in_labor', 'delivered', 'postnatal')),
ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS delivery_type TEXT CHECK (delivery_type IN ('normal', 'cesarean', 'assisted', 'forceps', 'vacuum')),
ADD COLUMN IF NOT EXISTS delivery_hospital TEXT,
ADD COLUMN IF NOT EXISTS delivery_complications JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS gestational_age_at_delivery INTEGER, -- Weeks at delivery
ADD COLUMN IF NOT EXISTS active_system TEXT DEFAULT 'matruraksha' CHECK (active_system IN ('matruraksha', 'santanraksha'));

COMMENT ON COLUMN public.mothers.delivery_status IS 'Tracks pregnancy-to-postnatal transition for frontend switching';
COMMENT ON COLUMN public.mothers.active_system IS 'Determines which frontend/agents are active: matruraksha (pregnancy) or santanraksha (postnatal+child)';

-- Create index for fast filtering
CREATE INDEX IF NOT EXISTS idx_mothers_active_system ON public.mothers(active_system, delivery_status);
CREATE INDEX IF NOT EXISTS idx_mothers_delivery_date ON public.mothers(delivery_date DESC) WHERE delivery_date IS NOT NULL;

-- ============================================================
-- Automated Delivery Completion Function
-- ============================================================

CREATE OR REPLACE FUNCTION public.complete_delivery(
  p_mother_id UUID,
  p_delivery_date TIMESTAMPTZ,
  p_delivery_type TEXT,
  p_delivery_hospital TEXT DEFAULT NULL,
  p_delivery_complications JSONB DEFAULT '[]'::jsonb,
  p_gestational_age_weeks INTEGER DEFAULT NULL,
  -- Child details
  p_child_name TEXT DEFAULT NULL,
  p_child_gender TEXT DEFAULT 'male',
  p_birth_weight_kg DECIMAL DEFAULT NULL,
  p_birth_length_cm DECIMAL DEFAULT NULL,
  p_birth_head_circumference_cm DECIMAL DEFAULT NULL,
  p_apgar_score_1min INTEGER DEFAULT NULL,
  p_apgar_score_5min INTEGER DEFAULT NULL,
  p_birth_complications JSONB DEFAULT '[]'::jsonb
)
RETURNS TABLE(
  mother_updated BOOLEAN,
  child_created UUID,
  vaccination_schedule_created BOOLEAN,
  system_switched TEXT
) AS $$
DECLARE
  v_child_id UUID;
  v_birth_date DATE;
BEGIN
  -- Extract birth date from delivery timestamp
  v_birth_date := p_delivery_date::DATE;
  
  -- 1. Update mother's delivery status
  UPDATE public.mothers
  SET 
    delivery_status = 'delivered',
    delivery_date = p_delivery_date,
    delivery_type = p_delivery_type,
    delivery_hospital = p_delivery_hospital,
    delivery_complications = p_delivery_complications,
    gestational_age_at_delivery = p_gestational_age_weeks,
    active_system = 'santanraksha' -- CRITICAL: Switch to SantanRaksha
  WHERE id = p_mother_id;
  
  -- 2. Create child record if name provided
  IF p_child_name IS NOT NULL THEN
    INSERT INTO public.children (
      mother_id,
      name,
      gender,
      birth_date,
      birth_weight_kg,
      birth_length_cm,
      birth_head_circumference_cm,
      delivery_type,
      gestational_age_weeks,
      apgar_score_1min,
      apgar_score_5min,
      birth_complications
    )
    VALUES (
      p_mother_id,
      p_child_name,
      p_child_gender,
      v_birth_date,
      p_birth_weight_kg,
      p_birth_length_cm,
      p_birth_head_circumference_cm,
      p_delivery_type,
      p_gestational_age_weeks,
      p_apgar_score_1min,
      p_apgar_score_5min,
      p_birth_complications
    )
    RETURNING id INTO v_child_id;
    
    -- 3. Auto-generate vaccination schedule for newborn
    PERFORM public.generate_vaccination_schedule(v_child_id, v_birth_date);
    
    RETURN QUERY SELECT TRUE, v_child_id, TRUE, 'santanraksha'::TEXT;
  ELSE
    -- No child created yet (can be added later)
    RETURN QUERY SELECT TRUE, NULL::UUID, FALSE, 'santanraksha'::TEXT;
  END IF;
  
  -- Log the transition
  RAISE NOTICE 'Mother % transitioned from MatruRaksha to SantanRaksha on %', p_mother_id, p_delivery_date;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.complete_delivery IS 'Automatically transitions mother from MatruRaksha (pregnancy) to SantanRaksha (postnatal+child) system';

-- ============================================================
-- View for MatruRaksha Frontend (Pregnant mothers only)
-- ============================================================

CREATE OR REPLACE VIEW public.matruraksha_mothers AS
SELECT 
  m.*,
  COUNT(DISTINCT a.id) as appointment_count,
  MAX(a.appointment_date) as next_appointment
FROM public.mothers m
LEFT JOIN public.appointments a ON a.mother_id = m.id AND a.status != 'completed'
WHERE m.active_system = 'matruraksha' 
  AND m.delivery_status IN ('pregnant', 'in_labor')
GROUP BY m.id;

COMMENT ON VIEW public.matruraksha_mothers IS 'Mothers active in MatruRaksha (pregnancy tracking) - shown in MatruRaksha frontend';

-- ============================================================
-- View for SantanRaksha Frontend (Delivered mothers + children)
-- ============================================================

CREATE OR REPLACE VIEW public.santanraksha_families AS
SELECT 
  m.id as mother_id,
  m.name as mother_name,
  m.phone as mother_phone,
  m.delivery_date,
  m.delivery_type,
  m.delivery_status,
  EXTRACT(DAY FROM (CURRENT_DATE - m.delivery_date::DATE))::INTEGER as days_postpartum,
  c.id as child_id,
  c.name as child_name,
  c.gender as child_gender,
  c.birth_date,
  EXTRACT(YEAR FROM AGE(CURRENT_DATE, c.birth_date))::INTEGER * 12 + 
    EXTRACT(MONTH FROM AGE(CURRENT_DATE, c.birth_date))::INTEGER as child_age_months,
  (CURRENT_DATE - c.birth_date)::INTEGER as child_age_days,
  c.photo_url as child_photo,
  -- Latest growth data
  (SELECT weight_kg FROM public.growth_records WHERE child_id = c.id ORDER BY measurement_date DESC LIMIT 1) as latest_weight,
  (SELECT height_cm FROM public.growth_records WHERE child_id = c.id ORDER BY measurement_date DESC LIMIT 1) as latest_height,
  (SELECT growth_status FROM public.growth_records WHERE child_id = c.id ORDER BY measurement_date DESC LIMIT 1) as growth_status,
  -- Vaccination status
  (SELECT COUNT(*) FROM public.vaccinations WHERE child_id = c.id AND status = 'completed') as vaccines_completed,
  (SELECT COUNT(*) FROM public.vaccinations WHERE child_id = c.id AND status = 'overdue') as vaccines_overdue
FROM public.mothers m
LEFT JOIN public.children c ON c.mother_id = m.id
WHERE m.active_system = 'santanraksha' 
  AND m.delivery_status IN ('delivered', 'postnatal')
ORDER BY m.delivery_date DESC;

COMMENT ON VIEW public.santanraksha_families IS 'Mothers+children active in SantanRaksha (postnatal+child) - shown in SantanRaksha frontend';

-- ============================================================
-- RLS Policies for Frontend Separation
-- ============================================================

-- MatruRaksha frontend should only see pregnant mothers
CREATE POLICY "MatruRaksha dashboard shows pregnant mothers only"
  ON public.mothers FOR SELECT
  USING (
    active_system = 'matruraksha' 
    AND delivery_status IN ('pregnant', 'in_labor')
  );

-- SantanRaksha frontend should only see delivered mothers
CREATE POLICY "SantanRaksha dashboard shows delivered mothers only"
  ON public.mothers FOR SELECT
  USING (
    active_system = 'santanraksha' 
    AND delivery_status IN ('delivered', 'postnatal')
  );

-- ============================================================
-- Trigger to auto-update delivery status
-- ============================================================

CREATE OR REPLACE FUNCTION public.check_postnatal_progression()
RETURNS TRIGGER AS $$
BEGIN
  -- Auto-update to 'postnatal' status after 6 weeks (42 days)
  IF NEW.delivery_status = 'delivered' 
     AND NEW.delivery_date IS NOT NULL
     AND EXTRACT(DAY FROM (CURRENT_DATE - NEW.delivery_date::DATE)) >= 42 THEN
    NEW.delivery_status := 'postnatal';
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_postnatal_progression ON public.mothers;
CREATE TRIGGER trigger_postnatal_progression
  BEFORE UPDATE ON public.mothers
  FOR EACH ROW
  EXECUTE FUNCTION public.check_postnatal_progression();

COMMENT ON FUNCTION public.check_postnatal_progression IS 'Auto-updates delivery_status to postnatal after 42 days (6 weeks)';

-- ============================================================
-- Migration Complete
-- ============================================================

COMMENT ON SCHEMA public IS 'MatruRaksha + SantanRaksha dual-system architecture with automatic frontend switching';
