# 🚀 SantanRaksha Quick Start Guide

## What You Can Do RIGHT NOW

### 1. Test the AI Agents (No DB setup required!)

```bash
# Navigate to backend
cd d:\SantanRaksha\backend

# Activate virtual environment (if exists)
.\.venv\Scripts\Activate.ps1

# Test PostnatalAgent
python
```

```python
>>> from agents.postnatal_agent import PostnatalAgent
>>> import asyncio
>>>
>>> agent = PostnatalAgent()
>>>
>>> # Test breastfeeding assessment
>>> result = asyncio.run(agent.assess_breastfeeding_issues({
...     'breastfeeding_issues': [{'issue': 'cracked_nipples', 'severity': 'moderate'}],
...     'frequency_per_day': 10,
...     'milk_supply': 'adequate'
... }))
>>>
>>> for rec in result['recommendations']:
...     print(rec)
```

**Expected Output:**
```
🌿 Apply breast milk on nipples after feeding (natural healing)
🩹 Use medical-grade lanolin cream (safe for baby)
✓ Check baby's latch - lips should flange out, not tucked in
⏰ Try feeding more frequently to avoid baby being too hungry (aggressive sucking)
```

### 2. Test VaccineAgent

```python
>>> from agents.vaccine_agent import VaccineAgent
>>>
>>> vaccine_agent = VaccineAgent()
>>>
>>> # Test side effect assessment
>>> result = asyncio.run(vaccine_agent.assess_side_effects({
...     'symptoms': ['fever', 'injection_site_pain'],
...     'hours_since_vaccination': 6,
...     'fever_temperature_celsius': 37.8,
...     'vaccine_name': 'Pentavalent-1'
... }))
>>>
>>> print(f"Risk Level: {result['risk_level']}")
>>> print(f"Normal Reaction: {result['is_normal_reaction']}")
>>> for rec in result['recommendations']:
...     print(rec)
```

### 3. Test PediatricAgent (Fever Assessment)

```python
>>> from agents.pediatric_agent import PediatricAgent
>>>
>>> peds_agent = PediatricAgent()
>>>
>>> # Test fever assessment for 8-month-old
>>> result = asyncio.run(peds_agent.assess_fever_risk({
...     'temperature_celsius': 38.5,
...     'age_months': 8,
...     'duration_days': 1,
...     'symptoms': ['fussiness'],
...     'weight_kg': 8.5
... }))
>>>
>>> print(f"Risk Level: {result['risk_level']}")
>>> for rec in result['recommendations']:
...     print(rec)
```

### 4. Test GrowthAgent (Z-Score Calculation)

```python
>>> from agents.growth_agent import GrowthAgent
>>>
>>> growth_agent = GrowthAgent()
>>>
>>> # Test z-score calculation for 12-month-old
>>> result = asyncio.run(growth_agent.calculate_z_scores({
...     'weight_kg': 9.5,
...     'height_cm': 75.0,
...     'age_months': 12,
...     'gender': 'male',
...     'head_circumference_cm': 46.0
... }))
>>>
>>> print(f"Growth Status: {result['growth_status']}")
>>> print(f"Z-Scores: {result['z_scores']}")
>>> print(f"Interpretation: {result['interpretation']}")
>>> for alert in result['alerts']:
...     print(alert)
```

---

## Database Setup (Required for Full System)

### Option 1: Supabase Cloud (Recommended)

1. **Apply Migration:**
   ```bash
   # Install Supabase CLI (if not installed)
   npm install -g supabase
   
   # Login to Supabase
   supabase login
   
   # Link your project
   supabase link --project-ref your-project-ref
   
   # Apply migration
   cd d:\SantanRaksha\infra\supabase
   supabase db push
   ```

2. **Verify Tables:**
   ```sql
   -- Run in Supabase SQL Editor
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('children', 'vaccinations', 'growth_records', 'milestones', 'postnatal_checkins');
   ```

3. **Test Vaccination Schedule Generator:**
   ```sql
   -- Insert test child
   INSERT INTO children (mother_id, name, gender, birth_date, birth_weight_kg)
   VALUES (1, 'Baby Test', 'male', '2026-01-01', 3.2)
   RETURNING id;
   
   -- Generate vaccine schedule (replace <child_id>)
   SELECT generate_vaccination_schedule('<child_id>', '2026-01-01');
   
   -- Verify vaccines created
   SELECT vaccine_name, due_date, status 
   FROM vaccinations 
   WHERE child_id = '<child_id>'
   ORDER BY due_date;
   ```

### Option 2: Local PostgreSQL

```bash
# Connect to your local PostgreSQL
psql -U postgres -d matruraksha

# Run migration
\i d:/SantanRaksha/infra/supabase/migration_santanraksha_v1.sql

# Verify
\dt public.children
```

---

## Agent Routing Test (Orchestrator)

```python
from agents.orchestrator import get_orchestrator
import asyncio

orchestrator = get_orchestrator()

# Test postnatal routing
message = "I'm having heavy bleeding after delivery, should I worry?"
mother_context = {
    'name': 'Test Mother',
    'preferred_language': 'en',
    'age': 28
}

response = asyncio.run(orchestrator.route_message(
    message=message,
    mother_context=mother_context,
    reports_context=[]
))

print(f"Agent routed to: {orchestrator.classify_intent(message)}")
print(f"Response: {response}")
```

**Expected**: Should route to `PostnatalAgent` and provide bleeding assessment.

---

## Sample Data for Testing

### Insert Test Mother & Child

```sql
-- Insert test mother
INSERT INTO mothers (name, phone, age, gravida, parity, bmi, location, preferred_language)
VALUES ('Priya Sharma', '9876543210', 28, 2, 1, 22.5, 'Pune', 'en')
RETURNING id;

-- Insert test child (replace <mother_id>)
INSERT INTO children (mother_id, name, gender, birth_date, birth_weight_kg, birth_length_cm, delivery_type, gestational_age_weeks)
VALUES (<mother_id>, 'Aarav Sharma', 'male', '2025-12-01', 3.2, 49.5, 'normal', 39)
RETURNING id;

-- Generate vaccination schedule
SELECT generate_vaccination_schedule('<child_id>', '2025-12-01');

-- Add growth record
INSERT INTO growth_records (
    child_id, measurement_date, age_months, age_days, 
    weight_kg, height_cm, head_circumference_cm, 
    measured_by
)
VALUES (
    '<child_id>', CURRENT_DATE, 1, 30, 
    4.5, 54.2, 37.0, 
    (SELECT id FROM user_profiles WHERE role = 'ASHA_WORKER' LIMIT 1)
);

-- Add postnatal checkin for mother
INSERT INTO postnatal_checkins (
    mother_id, checkin_date, days_postpartum,
    bleeding_status, breastfeeding_status, mood_score,
    pain_level, risk_level
)
VALUES (
    <mother_id>, CURRENT_DATE, 7,
    'normal', 'exclusive', 7,
    2, 'low'
);
```

---

## API Endpoint Testing (Once you add them to main.py)

### Register Child
```bash
curl -X POST http://localhost:8000/api/children \
  -H "Content-Type: application/json" \
  -d '{
    "mother_id": 1,
    "name": "Test Baby",
    "gender": "female",
    "birth_date": "2026-01-01",
    "birth_weight_kg": 3.1
  }'
```

### Get Overdue Vaccinations
```bash
curl http://localhost:8000/api/vaccinations/overdue
```

### Add Growth Record
```bash
curl -X POST http://localhost:8000/api/growth \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "uuid-here",
    "weight_kg": 8.5,
    "height_cm": 72.0,
    "age_months": 12
  }'
```

---

## Troubleshooting

### Issue: "Module not found: postnatal_agent"
**Solution:**
```bash
# Ensure you're in backend directory
cd d:\SantanRaksha\backend

# Check file exists
ls agents\postnatal_agent.py

# If using virtual environment, ensure it's activated
.\.venv\Scripts\Activate.ps1
```

### Issue: "GEMINI_API_KEY not found"
**Solution:**
```bash
# Add to .env file
echo "GEMINI_API_KEY=your-api-key-here" >> .env

# Verify
cat .env | Select-String "GEMINI_API_KEY"
```

### Issue: Database connection error
**Solution:**
```bash
# Check Supabase credentials in .env
cat .env | Select-String "SUPABASE"

# Test connection
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('✅ Connected')"
```

---

## Next Steps After Testing

1. **Add API Endpoints to `main.py`**
   - Children CRUD
   - Vaccination tracking
   - Growth records
   - Postnatal check-ins

2. **Build Frontend Components**
   - Child profile cards
   - Vaccination schedule calendar
   - Growth chart visualizations
   - Postnatal symptom tracker

3. **Deploy Migration to Production Supabase**
   ```bash
   supabase link --project-ref your-production-ref
   supabase db push
   ```

4. **Set Up Scheduled Jobs**
   - Daily: `update_overdue_vaccinations()`
   - Weekly: Growth faltering detection
   - Daily: Vaccine reminder SMS/WhatsApp

---

## Quick Reference: Agent Capabilities

| Agent | Best For | Example Queries |
|-------|----------|----------------|
| **PostnatalAgent** | Bleeding, breastfeeding, mental health | "Cracked nipples while feeding", "Feeling sad after delivery" |
| **PediatricAgent** | Fever, diarrhea, cough, general illness | "Baby has 101°F fever, what to do?", "Baby vomiting after feeding" |
| **VaccineAgent** | Schedule, side effects, safety | "When is next vaccine due?", "Fever after BCG vaccine" |
| **GrowthAgent** | Weight, malnutrition, feeding | "Baby not gaining weight", "What foods to start at 6 months?" |

---

**Ready to test?**: Start with agent testing (no setup required), then move to database setup when ready!

🎯 **Goal**: Get all 4 agents responding correctly → Deploy DB migration → Add API endpoints → Build frontend
