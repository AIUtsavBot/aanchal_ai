# SantanRaksha API Specification

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints require authentication via JWT token or Supabase session.
Include in headers:
```
Authorization: Bearer <token>
```

---

## 1. Children Management

### 1.1 Register Child
**`POST /api/children`**

**Request Body:**
```json
{
  "mother_id": 1,
  "name": "Aarav Sharma",
  "gender": "male",
  "birth_date": "2026-01-01",
  "birth_weight_kg": 3.2,
  "birth_length_cm": 49.5,
  "birth_head_circumference_cm": 34.5,
  "delivery_type": "normal",
  "gestational_age_weeks": 39,
  "apgar_score_1min": 8,
  "apgar_score_5min": 9,
  "blood_group": "O+",
  "birth_complications": ["jaundice"],
  "generate_vaccine_schedule": true
}
```

**Response `201 Created`:**
```json
{
  "id": "uuid",
  "mother_id": 1,
  "name": "Aarav Sharma",
  "age_months": 0,
  "age_days": 1,
  "next_vaccine_due": "BCG",
  "created_at": "2026-01-01T10:00:00Z",
  "vaccination_schedule_generated": true
}
```

---

### 1.2 Get Child Profile
**`GET /api/children/{child_id}`**

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "mother_id": 1,
  "name": "Aarav Sharma",
  "gender": "male",
  "birth_date": "2026-01-01",
  "age_months": 6,
  "age_days": 180,
  "photo_url": "https://supabase.co/storage/...",
  "health_summary": {
    "latest_weight_kg": 7.5,
    "latest_height_cm": 66.0,
    "growth_status": "normal",
    "vaccinations_completed": 10,
    "vaccinations_pending": 4,
    "next_vaccine_due": {
      "name": "MR-1",
      "due_date": "2026-10-01",
      "days_until_due": 90
    },
    "milestones_achieved": 8,
    "milestones_delayed": 0
  },
  "birth_details": {
    "weight_kg": 3.2,
    "length_cm": 49.5,
    "apgar_scores": {"1min": 8, "5min": 9},
    "gestational_age_weeks": 39
  }
}
```

---

### 1.3 List Mother's Children
**`GET /api/mothers/{mother_id}/children`**

**Response `200 OK`:**
```json
{
  "mother_id": 1,
  "children": [
    {
      "id": "uuid-1",
      "name": "Aarav",
      "age_months": 24,
      "age_years_months": "2 years 0 months",
      "latest_weight_kg": 12.5,
      "growth_status": "normal",
      "next_vaccine_due": "DPT Booster 2",
      "overdue_vaccines_count": 0
    },
    {
      "id": "uuid-2",
      "name": "Diya",
      "age_months": 6,
      "age_years_months": "6 months",
      "latest_weight_kg": 7.2,
      "growth_status": "normal",
      "next_vaccine_due": "MR-1",
      "overdue_vaccines_count": 1
    }
  ],
  "total_children": 2
}
```

---

## 2. Vaccinations

### 2.1 Get Vaccination Schedule
**`GET /api/children/{child_id}/vaccinations`**

**Query Parameters:**
- `status` (optional): `pending`, `completed`, `overdue`, `all` (default: `all`)

**Response `200 OK`:**
```json
{
  "child_id": "uuid",
  "vaccinations": [
    {
      "id": "uuid",
      "vaccine_name": "BCG",
      "due_date": "2026-01-01",
      "administered_date": "2026-01-01",
      "status": "completed",
      "batch_number": "BCG2026-001",
      "administered_by": "ASHA Seema Patil",
      "site": "left_arm"
    },
    {
      "id": "uuid",
      "vaccine_name": "MR-1",
      "due_date": "2026-10-01",
      "status": "pending",
      "days_until_due": 90,
      "reminder_sent": false
    }
  ],
  "summary": {
    "total": 19,
    "completed": 10,
    "pending": 8,
    "overdue": 1
  }
}
```

---

### 2.2 Mark Vaccine Administered
**`PUT /api/vaccinations/{vaccination_id}/administer`**

**Request Body:**
```json
{
  "administered_date": "2026-01-15",
  "batch_number": "MR2026-042",
  "administered_by": "ASHA Seema Patil",
  "administered_at_facility": "Pune PHC",
  "site": "right_thigh",
  "adverse_reaction": "mild fever",
  "adverse_reaction_severity": "mild",
  "notes": "No issues during administration"
}
```

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "vaccine_name": "MR-1",
  "status": "completed",
  "administered_date": "2026-01-15",
  "next_vaccine": {
    "name": "JE-1",
    "due_date": "2026-10-01"
  }
}
```

---

### 2.3 Get Overdue Vaccinations (ASHA Dashboard)
**`GET /api/vaccinations/overdue`**

**Query Parameters:**
- `asha_worker_id` (optional): Filter by ASHA worker
- `days_overdue` (optional): Minimum days overdue (default: 0)

**Response `200 OK`:**
```json
{
  "overdue_count": 15,
  "vaccinations": [
    {
      "vaccination_id": "uuid",
      "child_name": "Aarav Sharma",
      "child_id": "uuid",
      "mother_name": "Priya Sharma",
      "mother_phone": "9876543210",
      "vaccine_name": "MR-1",
      "due_date": "2025-12-01",
      "days_overdue": 54,
      "priority": "high"
    }
  ]
}
```

---

### 2.4 Send Vaccine Reminders
**`POST /api/vaccinations/send-reminders`**

**Request Body:**
```json
{
  "days_before_due": 3,
  "channel": "sms",  // or "whatsapp", "telegram"
  "asha_worker_id": "uuid" // optional
}
```

**Response `200 OK`:**
```json
{
  "reminders_sent": 25,
  "children_notified": 18,
  "mothers_notified": 15,
  "asha_workers_notified": 3
}
```

---

## 3. Growth Monitoring

### 3.1 Add Growth Record
**`POST /api/growth`**

**Request Body:**
```json
{
  "child_id": "uuid",
  "measurement_date": "2026-01-15",
  "weight_kg": 8.5,
  "height_cm": 72.0,
  "head_circumference_cm": 45.5,
  "muac_cm": 13.5,
  "measured_by": "uuid",  // ASHA worker user_profile_id
  "measurement_location": "anganwadi",
  "notes": "Child active and healthy"
}
```

**Response `201 Created`:**
```json
{
  "id": "uuid",
  "child_id": "uuid",
  "measurement_date": "2026-01-15",
  "age_months": 12,
  "weight_kg": 8.5,
  "height_cm": 72.0,
  "z_scores": {
    "weight_for_age": -0.5,
    "height_for_age": 0.2,
    "weight_for_height": -0.3,
    "head_circumference": 0.1
  },
  "growth_status": "normal",
  "alert_generated": false,
  "recommendations": [
    "Continue current feeding practices",
    "Next measurement in 1 month"
  ]
}
```

---

### 3.2 Get Growth History & Chart
**`GET /api/children/{child_id}/growth`**

**Query Parameters:**
- `limit` (optional): Number of records (default: 20)
- `from_date` (optional): Filter from date

**Response `200 OK`:**
```json
{
  "child_id": "uuid",
  "growth_records": [
    {
      "measurement_date": "2026-01-15",
      "age_months": 12,
      "weight_kg": 8.5,
      "height_cm": 72.0,
      "z_scores": {
        "weight_for_age": -0.5,
        "height_for_age": 0.2
      },
      "growth_status": "normal"
    }
  ],
  "growth_trend": {
    "weight_velocity": "normal",  // weight gain rate
    "height_velocity": "normal",
    "crossing_percentiles": false  // crossing >2 lines = concern
  },
  "chart_data": {
    "who_median": [3.2, 4.5, 5.6, 6.4, 7.0, 7.5, 7.9, 8.3, 8.6, 9.0, 9.2, 9.5, 9.7],
    "child_actual": [3.2, 4.3, 5.4, 6.2, 6.8, 7.3, 7.8, 8.1, 8.4, 8.6, 8.5, 8.5],
    "percentiles": {
      "p3": [...],
      "p15": [...],
      "p50": [...],
      "p85": [...],
      "p97": [...]
    }
  }
}
```

---

### 3.3 Get Growth Alerts (Doctor/ASHA Dashboard)
**`GET /api/growth/alerts`**

**Query Parameters:**
- `growth_status` (optional): `severe_acute_malnutrition`, `moderate_acute_malnutrition`, `stunted`, etc.

**Response `200 OK`:**
```json
{
  "total_alerts": 8,
  "children": [
    {
      "child_id": "uuid",
      "child_name": "Rahul Kumar",
      "age_months": 18,
      "growth_status": "moderate_acute_malnutrition",
      "latest_z_scores": {
        "weight_for_height": -2.3
      },
      "alert_date": "2026-01-10",
      "action_needed": "Enhanced feeding plan, weekly monitoring"
    }
  ]
}
```

---

## 4. Postnatal Care

### 4.1 Submit Postnatal Check-in
**`POST /api/postnatal/checkin`**

**Request Body:**
```json
{
  "mother_id": 1,
  "checkin_date": "2026-01-08",
  "days_postpartum": 7,
  "bleeding_status": "normal",
  "bleeding_color": "brown",
  "pad_changes_per_day": 3,
  "pain_level": 2,
  "temperature_celsius": 37.2,
  "wound_type": "cesarean",
  "wound_healing": "normal",
  "breastfeeding_status": "exclusive",
  "breastfeeding_frequency_per_day": 10,
  "breastfeeding_issues": [
    {"issue": "cracked_nipples", "severity": "mild"}
  ],
  "infant_latching_well": true,
  "milk_supply": "adequate",
  "mood_score": 7,
  "has_crying_episodes": false,
  "sleep_quality": "fair",
  "epds_score": 8,
  "recorded_by": "uuid",  // ASHA worker
  "notes": "Recovery progressing well"
}
```

**Response `201 Created`:**
```json
{
  "id": "uuid",
  "mother_id": 1,
  "checkin_date": "2026-01-08",
  "days_postpartum": 7,
  "risk_level": "low",
  "depression_risk": "low",
  "immediate_action_needed": false,
  "recommendations": [
    "Continue exclusive breastfeeding",
    "Apply breast milk on nipples for healing",
    "Next checkup at 14 days postpartum"
  ],
  "next_checkin_due": "2026-01-15"
}
```

---

### 4.2 Get Postnatal Timeline
**`GET /api/mothers/{mother_id}/postnatal-timeline`**

**Response `200 OK`:**
```json
{
  "mother_id": 1,
  "delivery_date": "2026-01-01",
  "days_postpartum": 14,
  "checkins_completed": [3, 7],
  "checkins_upcoming": [14, 28, 42],
  "checkin_history": [
    {
      "days_postpartum": 7,
      "risk_level": "low",
      "bleeding_status": "normal",
      "breastfeeding_status": "exclusive",
      "mood_score": 7
    }
  ],
  "suman_protocol_status": {
    "checkin_48hr": "completed",
    "checkin_3days": "completed",
    "checkin_7days": "completed",
    "checkin_14days": "pending",
    "checkin_28days": "pending",
    "checkin_42days": "pending"
  }
}
```

---

### 4.3 Get High-Risk Postnatal Cases (Doctor Dashboard)
**`GET /api/postnatal/high-risk`**

**Response `200 OK`:**
```json
{
  "high_risk_count": 4,
  "mothers": [
    {
      "mother_id": 1,
      "mother_name": "Priya Sharma",
      "days_postpartum": 10,
      "risk_level": "high",
      "risk_factors": ["heavy_bleeding", "low_mood"],
      "last_checkin_date": "2026-01-10",
      "immediate_action_needed": true,
      "contact_phone": "9876543210",
      "assigned_asha": "Seema Patil"
    }
  ]
}
```

---

## 5. AI Agent Queries

### 5.1 Ask Postnatal Agent
**`POST /api/agents/postnatal/query`**

**Request Body:**
```json
{
  "mother_id": 1,
  "query": "I'm having cracked nipples while breastfeeding, what should I do?",
  "context": {
    "days_postpartum": 10,
    "breastfeeding_status": "exclusive",
    "previous_issues": ["engorgement"]
  }
}
```

**Response `200 OK`:**
```json
{
  "agent": "PostnatalAgent",
  "response": "Cracked nipples are common in the first 2 weeks. Here's what you can do:\n\n1. Apply breast milk on nipples after feeding (natural healing)\n2. Use medical-grade lanolin cream\n3. Check baby's latch...",
  "clinical_assessment": {
    "issue_severity": "mild",
    "recommendations": [
      "Apply breast milk after feeding",
      "Check latch technique",
      "Continue breastfeeding (don't skip)"
    ],
    "referral_needed": false
  },
  "follow_up_recommended": "7 days"
}
```

---

### 5.2 Ask Pediatric Agent
**`POST /api/agents/pediatric/query`**

**Request Body:**
```json
{
  "child_id": "uuid",
  "query": "My baby has 102°F fever for 6 hours, should I worry?",
  "context": {
    "age_months": 8,
    "weight_kg": 8.0,
    "symptoms": ["fever", "fussiness"],
    "temperature_celsius": 38.9
  }
}
```

**Response `200 OK`:**
```json
{
  "agent": "PediatricAgent",
  "response": "For an 8-month-old with 102°F fever:\n\n1. Give paracetamol: 2.5ml every 4-6 hours\n2. Lukewarm sponging...",
  "clinical_assessment": {
    "risk_level": "medium",
    "fever_category": "moderate",
    "immediate_care_needed": false,
    "recommendations": [
      "Paracetamol (Calpol) 2.5ml every 4-6 hours",
      "Monitor every 2-3 hours",
      "See doctor if fever >24 hours or worsens"
    ],
    "danger_signs_present": false
  }
}
```

---

## Error Responses

### `400 Bad Request`
```json
{
  "error": "Validation Error",
  "details": {
    "field": "birth_date",
    "message": "birth_date cannot be in future"
  }
}
```

### `404 Not Found`
```json
{
  "error": "Child not found",
  "child_id": "uuid"
}
```

### `403 Forbidden`
```json
{
  "error": "Unauthorized",
  "message": "ASHA worker can only view children in assigned area"
}
```

### `500 Internal Server Error`
```json
{
  "error": "Internal Server Error",
  "message": "Database connection failed"
}
```

---

## Rate Limiting

```
100 requests per minute per user
1000 requests per hour per user
```

## Pagination

For list endpoints:
```
GET /api/children?page=1&limit=20

Response headers:
X-Total-Count: 150
X-Page: 1
X-Page-Size: 20
X-Total-Pages: 8
```

---

## Implementation Priority

1. **Phase 1** (Core CRUD):
   - `POST /api/children`
   - `GET /api/children/{child_id}`
   - `POST /api/growth`
   - `POST /api/postnatal/checkin`

2. **Phase 2** (Dashboards):
   - `GET /api/vaccinations/overdue`
   - `GET /api/growth/alerts`
   - `GET /api/postnatal/high-risk`

3. **Phase 3** (Advanced):
   - `POST /api/agents/*/query`
   - `POST /api/vaccinations/send-reminders`
   - Growth chart generation

---

**Total Endpoints**: 15+  
**Estimated Implementation Time**: 8-12 hours for Phase 1  
**Dependencies**: Database migration must be completed first
