# MatruRaksha AI - API Endpoints Documentation

> Complete API reference for the MatruRaksha Maternal Health Monitoring System

**Base URL**: `http://localhost:8000` (Development) | `https://matruraksha-ai-event.onrender.com` (Production)

---

## Table of Contents

1. [Health Check](#health-check)
2. [Mother Management](#mother-management)
3. [Risk Assessment](#risk-assessment)
4. [Document Analysis](#document-analysis)
5. [Dashboard](#dashboard)
6. [AI Agents](#ai-agents)

---

## Health Check

### GET `/health`
Get the current health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T09:30:00.000Z",
  "service": "MatruRaksha AI Backend",
  "version": "2.0.0",
  "supabase_connected": true,
  "telegram_bot_token": "✅ Set",
  "telegram_polling": "🟢 Active",
  "gemini_ai": "🤖 Active",
  "ai_agents": "🤖 Active"
}
```

---

## Mother Management

### POST `/mothers/register`
Register a new pregnant mother in the system.

**Request Body:**
```json
{
  "name": "Anjali Sharma",
  "phone": "+919876543210",
  "age": 28,
  "gravida": 2,
  "parity": 1,
  "bmi": 24.5,
  "location": "Pune",
  "preferred_language": "hi",
  "telegram_chat_id": "123456789",
  "due_date": "2026-06-15"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mother registered successfully",
  "mother_id": "uuid-string",
  "data": { ... }
}
```

---

### GET `/mothers`
Get all registered mothers.

**Response:**
```json
{
  "status": "success",
  "count": 25,
  "data": [
    {
      "id": "uuid",
      "name": "Anjali Sharma",
      "phone": "+919876543210",
      "age": 28,
      "gravida": 2,
      "parity": 1,
      "bmi": 24.5,
      "location": "Pune",
      "risk_level": "LOW",
      "created_at": "2026-01-01T10:00:00Z"
    }
  ]
}
```

---

### GET `/mothers/{mother_id}`
Get a specific mother's details by ID.

**Path Parameters:**
- `mother_id` (string, required): The UUID of the mother

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "name": "Anjali Sharma",
    "phone": "+919876543210",
    "age": 28,
    "gravida": 2,
    "parity": 1,
    "bmi": 24.5,
    "location": "Pune",
    "preferred_language": "hi",
    "telegram_chat_id": "123456789",
    "due_date": "2026-06-15",
    "medical_history": { ... },
    "asha_worker_id": 1,
    "doctor_id": 2,
    "created_at": "2026-01-01T10:00:00Z"
  }
}
```

---

## Risk Assessment

### POST `/risk-assessment`
Submit a risk assessment for a mother.

**Request Body:**
```json
{
  "mother_id": "uuid-string",
  "systolic_bp": 140,
  "diastolic_bp": 90,
  "heart_rate": 85,
  "blood_glucose": 120.5,
  "hemoglobin": 11.5,
  "proteinuria": 0,
  "edema": 0,
  "headache": 1,
  "vision_changes": 0,
  "epigastric_pain": 0,
  "vaginal_bleeding": 0,
  "notes": "Patient reports mild headache"
}
```

**Response:**
```json
{
  "status": "success",
  "assessment_id": "uuid",
  "risk_score": 0.35,
  "risk_level": "LOW",
  "risk_factors": ["Headache"],
  "recommendations": ["Monitor blood pressure", "Rest advised"]
}
```

---

### GET `/risk-assessment/{mother_id}`
Get all risk assessments for a mother.

**Path Parameters:**
- `mother_id` (string, required): The UUID of the mother

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "id": "uuid",
      "risk_score": 0.35,
      "risk_level": "LOW",
      "risk_factors": ["Headache"],
      "assessed_at": "2026-01-05T09:00:00Z"
    }
  ]
}
```

---

## Document Analysis

### POST `/reports/upload`
Upload a medical document/report for AI analysis.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF, JPG, PNG, or WebP (max 10MB) |
| `mother_id` | string | Yes | UUID of the mother |
| `uploader_id` | string | No | UUID of the uploader |
| `uploader_role` | string | No | Role of uploader (ASHA_WORKER, DOCTOR) |
| `uploader_name` | string | No | Name of the uploader |

**Response:**
```json
{
  "success": true,
  "message": "Report uploaded and analysis started",
  "report_id": "uuid",
  "file_url": "https://supabase.storage/...",
  "analysis_status": "processing"
}
```

---

### POST `/analyze-report`
Trigger AI analysis on an uploaded report.

**Request Body:**
```json
{
  "report_id": "uuid",
  "mother_id": "uuid",
  "file_url": "https://storage.url/file.pdf",
  "file_type": "application/pdf"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report analyzed successfully",
  "status": "completed",
  "risk_level": "moderate",
  "concerns": [
    "Low hemoglobin detected (9.5 g/dL)",
    "Elevated blood pressure"
  ],
  "recommendations": [
    "Iron supplementation recommended",
    "Follow-up with doctor in 1 week"
  ],
  "analysis": {
    "extracted_data": {
      "hemoglobin": 9.5,
      "blood_pressure_systolic": 145,
      "blood_pressure_diastolic": 92
    },
    "analyzed_with": "Google Gemini AI"
  }
}
```

---

## Dashboard

### GET `/dashboard`
Get comprehensive dashboard data for the logged-in user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "id": "uuid",
    "role": "ASHA_WORKER",
    "name": "Seema Patil"
  },
  "stats": {
    "total_mothers": 15,
    "high_risk": 3,
    "moderate_risk": 5,
    "low_risk": 7,
    "pending_checkups": 4
  },
  "recent_activities": [ ... ],
  "upcoming_appointments": [ ... ]
}
```

---

### GET `/dashboard/mothers/{mother_id}`
Get detailed dashboard view for a specific mother.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "mother": { ... },
  "health_timeline": [ ... ],
  "risk_trend": [ ... ],
  "medications": [ ... ],
  "appointments": [ ... ],
  "recent_reports": [ ... ]
}
```

---

## AI Agents

### POST `/agent/query`
Send a query to the AI agent orchestrator.

**Request Body:**
```json
{
  "mother_id": "uuid",
  "query": "What diet should I follow during my third trimester?",
  "context": {
    "current_week": 32,
    "conditions": ["gestational_diabetes"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": "During your third trimester with gestational diabetes...",
  "agents_used": ["nutrition_agent", "care_agent"],
  "confidence": 0.92,
  "sources": ["WHO Guidelines", "ICMR Nutrition Guidelines"]
}
```

---

### POST `/daily-checkin`
Submit a daily health check-in from a mother.

**Request Body:**
```json
{
  "mother_id": "uuid",
  "date": "2026-01-05",
  "weight": 65.5,
  "bp_systolic": 118,
  "bp_diastolic": 76,
  "symptoms": ["fatigue", "mild_headache"],
  "medications_taken": true,
  "feeling_today": "good",
  "notes": "Slept well last night"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Check-in recorded",
  "checkin_id": "uuid",
  "ai_feedback": "Your vitals look good! Keep staying hydrated.",
  "follow_up_needed": false
}
```

---

## Error Responses

All endpoints may return the following error structure:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400
}
```

**Common Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Supabase not connected |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **General endpoints**: 100 requests/minute
- **AI analysis endpoints**: 10 requests/minute
- **Upload endpoints**: 20 requests/minute

---

*Last updated: January 2026*
