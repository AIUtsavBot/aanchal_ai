-- ...empty file...
-- 1. Insert into mothers (UUID id)
INSERT INTO public.mothers (
  id, name, phone, age, gravida, parity, bmi, location, preferred_language, telegram_chat_id, due_date
) VALUES (
  gen_random_uuid(), 'Radha Patel', '9206432482', 30, 1, 0, 23.8, 'Ahmedabad', 'en', '1345507750', '2026-07-20'
);

-- 2. Insert into appointments (UUID id, mother_id by subquery, assigned_asha can be NULL or a valid UUID)
INSERT INTO public.appointments (
  id, mother_id, facility, appointment_date, assigned_asha, status, notes, appointment_type
) VALUES (
  gen_random_uuid(),
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  'Ahmedabad Primary Health Center',
  '2025-11-28 11:00:00+05:30',
  NULL,
  'scheduled',
  'Initial antenatal consultation',
  'Consultation'
);

-- 3. Insert into health_timeline (UUID id, mother_id by subquery)
INSERT INTO public.health_timeline (
  id, mother_id, week_number, date, weight, bp_systolic, bp_diastolic, hemoglobin, symptoms,
  risk_level, risk_score, ai_assessment, entry_type, reported_by, created_at
) VALUES (
  gen_random_uuid(),
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  14,  -- Example gestational week
  '2025-11-23',
  59.0,
  118,
  80,
  13.2,
  '{"concern":"none"}'::jsonb,
  'low',
  2.0,
  '{"assessment":"routine labs"}'::jsonb,
  'first_visit',
  'Radha Patel',
  now()
);

-- 4. Insert into medical_reports (UUID id)
INSERT INTO public.medical_reports (
  id, mother_id, telegram_chat_id, file_name, file_type, file_url, file_path, uploaded_at, analysis_status, analysis_result, extracted_metrics, analyzed_at, error_message
) VALUES (
  gen_random_uuid(),
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  '1345507750',
  'rp_initial_report.pdf',
  'pdf',
  '/files/rp_initial_report.pdf',
  '/files/rp_initial_report.pdf',
  now(),
  'completed',
  '{"summary":"All normal"}'::jsonb,
  '{"weight":59.0,"bp":"118/80"}'::jsonb,
  now(),
  NULL
);

-- 5. Insert into health_metrics (UUID id)
INSERT INTO public.health_metrics (
  id, mother_id, weight_kg, blood_pressure_systolic, blood_pressure_diastolic, hemoglobin, blood_sugar, measured_at, notes
) VALUES (
  gen_random_uuid(),
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  59.0,
  118,
  80,
  13.2,
  95.0,
  now(),
  'First measurement, healthy'
);

-- 6. Insert into context_memory (auto-increment bigint id; omit id from insert)
INSERT INTO public.context_memory (
  mother_id, memory_key, memory_value, memory_type, source
) VALUES (
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  'intro_visit',
  '2025-11-23',
  'date',
  'system'
);

-- 7. Insert into conversations (auto-increment bigint id; omit id)
INSERT INTO public.conversations (
  mother_id, message_role, message_content, context_used, agent_response
) VALUES (
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  'user',
  'Hello, this is my first checkup.',
  '{"visit_stage":"initial"}'::jsonb,
  '{"advice":"lab investigations suggested"}'::jsonb
);

-- 8. Insert into agents (auto-increment bigint id; omit id)
INSERT INTO public.agents (
  mother_id, agent_config
) VALUES (
  (SELECT id FROM public.mothers WHERE phone='9206432482'),
  '{"agent_type":"health_advisor","language":"en"}'::jsonb
);
