# 🚀 MatruRaksha API Endpoints Documentation

> Complete reference for all REST API endpoints in the MatruRaksha backend.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Authentication](#-authentication)
- [Core Endpoints](#-core-endpoints)
- [Mother Management](#-mother-management)
- [Risk Assessment](#-risk-assessment)
- [Report Analysis](#-report-analysis)
- [Admin Dashboard](#-admin-dashboard)
- [Registration & Approvals](#-registration--approvals)
- [Analytics](#-analytics)
- [Error Handling](#-error-handling)

---

## 🔍 Overview

**Base URL:** `http://localhost:8000` (development) | `https://your-domain.com` (production)

**API Documentation:** Interactive docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

**Content-Type:** `application/json`

**Authentication:** Bearer token in `Authorization` header (Supabase JWT)

---

## 🔐 Authentication

All protected endpoints require a valid JWT token from Supabase Auth.

**Header Format:**
```
Authorization: Bearer <your-jwt-token>
```

### `POST /auth/signin`
Sign in with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "DOCTOR"
  }
}
```

---

### `POST /auth/signup`
Register a new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "full_name": "Dr. John Doe",
  "role": "DOCTOR",
  "phone": "+919876543210"
}
```

**Response:** `201 Created`
```json
{
  "message": "Registration request submitted",
  "status": "pending_approval"
}
```

---

### `POST /auth/signout`
Sign out current user.

**Response:** `200 OK`
```json
{
  "message": "Successfully signed out"
}
```

---

### `GET /auth/profile`
Get current user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Dr. John Doe",
  "role": "DOCTOR",
  "phone": "+919876543210",
  "is_active": true,
  "assigned_area": "Mumbai"
}
```

---

### `PUT /auth/profile`
Update user profile.

**Request Body:**
```json
{
  "full_name": "Dr. John Smith",
  "phone": "+919876543211",
  "assigned_area": "Pune"
}
```

**Response:** `200 OK`

---

### `POST /auth/upload-cert`
Upload doctor certification document.

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Certificate file (PDF, JPG, PNG)
- `user_id`: UUID of the user

**Response:** `200 OK`
```json
{
  "url": "https://storage.supabase.co/documents/cert_123.pdf",
  "message": "Certificate uploaded successfully"
}
```

---

## 📌 Core Endpoints

### `GET /`
Root endpoint with API information.

**Response:** `200 OK`
```json
{
  "name": "MatruRaksha AI API",
  "version": "2.3.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### `GET /health`
Health check endpoint for monitoring.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "telegram_bot": "active",
  "timestamp": "2026-01-03T12:00:00Z"
}
```

---

## 👩‍🍼 Mother Management

### `POST /mothers/register`
Register a new mother in the system.

**Request Body:**
```json
{
  "name": "Priya Sharma",
  "phone": "9876543210",
  "age": 28,
  "gravida": 2,
  "parity": 1,
  "bmi": 22.5,
  "location": "Mumbai",
  "preferred_language": "hi",
  "telegram_chat_id": "123456789"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Priya Sharma",
  "phone": "9876543210",
  "message": "Mother registered successfully"
}
```

---

### `GET /mothers`
List all registered mothers.

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset
- `risk_level` (optional): Filter by risk level (HIGH, MODERATE, LOW)

**Response:** `200 OK`
```json
{
  "mothers": [
    {
      "id": 1,
      "name": "Priya Sharma",
      "phone": "9876543210",
      "age": 28,
      "risk_level": "LOW",
      "doctor_id": 1,
      "asha_worker_id": 2
    }
  ],
  "total": 100
}
```

---

### `GET /mothers/{mother_id}`
Get a specific mother's details.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Priya Sharma",
  "phone": "9876543210",
  "age": 28,
  "gravida": 2,
  "parity": 1,
  "bmi": 22.5,
  "location": "Mumbai",
  "preferred_language": "hi",
  "telegram_chat_id": "123456789",
  "doctor": { "id": 1, "name": "Dr. Meera Shah" },
  "asha_worker": { "id": 2, "name": "Seema Patil" },
  "latest_risk_assessment": { ... }
}
```

---

## ⚠️ Risk Assessment

### `POST /risk/assess`
Submit a new risk assessment.

**Request Body:**
```json
{
  "mother_id": 1,
  "systolic_bp": 140,
  "diastolic_bp": 90,
  "hemoglobin": 10.5,
  "blood_sugar": 95,
  "weight": 65.5,
  "symptoms": ["headache", "swelling"],
  "notes": "Patient reports mild headache"
}
```

**Response:** `200 OK`
```json
{
  "assessment_id": "uuid",
  "risk_level": "MODERATE",
  "risk_score": 65,
  "factors": [
    "Elevated blood pressure (140/90)",
    "Mild anemia (Hb: 10.5)"
  ],
  "recommendations": [
    "Monitor BP daily",
    "Increase iron-rich foods",
    "Schedule follow-up in 3 days"
  ],
  "emergency": false
}
```

---

### `GET /risk/mother/{mother_id}`
Get all risk assessments for a mother.

**Response:** `200 OK`
```json
{
  "assessments": [
    {
      "id": "uuid",
      "created_at": "2026-01-03T10:00:00Z",
      "risk_level": "MODERATE",
      "risk_score": 65,
      "systolic_bp": 140,
      "diastolic_bp": 90,
      "hemoglobin": 10.5
    }
  ]
}
```

---

## 📄 Report Analysis

### `POST /analyze-report`
Analyze a medical report using Gemini AI.

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Report file (PDF, JPG, PNG)
- `mother_id`: Mother's ID

**Response:** `200 OK`
```json
{
  "report_id": "uuid",
  "analysis_summary": "Overall healthy pregnancy...",
  "health_metrics": {
    "hemoglobin": 11.5,
    "blood_sugar": 90,
    "blood_pressure": "120/80"
  },
  "concerns": ["Slight vitamin D deficiency"],
  "recommendations": ["Increase sun exposure", "Vitamin D supplements"]
}
```

---

### `GET /reports/{mother_id}`
Get all reports for a mother.

**Response:** `200 OK`
```json
{
  "reports": [
    {
      "id": "uuid",
      "filename": "lab_report_jan2026.pdf",
      "upload_date": "2026-01-02T15:00:00Z",
      "analysis_summary": "...",
      "processed": true
    }
  ]
}
```

---

### `GET /reports/telegram/{telegram_chat_id}`
Get reports by Telegram chat ID.

**Response:** `200 OK`

---

## 👨‍💼 Admin Dashboard

### `GET /admin/stats`
Get dashboard statistics.

**Response:** `200 OK`
```json
{
  "total_mothers": 150,
  "high_risk_count": 15,
  "moderate_risk_count": 45,
  "low_risk_count": 90,
  "total_doctors": 10,
  "total_asha_workers": 25,
  "pending_approvals": 3
}
```

---

### `GET /admin/full`
Combined endpoint for all admin dashboard data (optimized).

**Response:** `200 OK`
```json
{
  "stats": { ... },
  "doctors": [ ... ],
  "asha_workers": [ ... ],
  "mothers": [ ... ],
  "pending_requests": [ ... ]
}
```

---

### `GET /admin/doctors`
List all doctors.

**Response:** `200 OK`
```json
{
  "doctors": [
    {
      "id": 1,
      "name": "Dr. Meera Shah",
      "email": "meera@hospital.com",
      "phone": "9100000001",
      "assigned_area": "Pune",
      "is_active": true,
      "patients_count": 25
    }
  ]
}
```

---

### `GET /admin/doctors/{id}`
Get doctor details.

### `PUT /admin/doctors/{id}`
Update doctor information.

### `DELETE /admin/doctors/{id}`
Deactivate a doctor.

---

### `GET /admin/asha-workers`
List all ASHA workers.

### `GET /admin/asha-workers/{id}`
Get ASHA worker details.

### `PUT /admin/asha-workers/{id}`
Update ASHA worker information.

### `DELETE /admin/asha-workers/{id}`
Deactivate an ASHA worker.

---

### `GET /admin/mothers`
List all mothers with assignments.

### `POST /admin/mothers/{id}/assign-asha`
Assign a mother to an ASHA worker.

**Request Body:**
```json
{
  "asha_worker_id": 2
}
```

---

### `POST /admin/mothers/{id}/assign-doctor`
Assign a mother to a doctor.

**Request Body:**
```json
{
  "doctor_id": 1
}
```

---

### `POST /admin/mothers/{id}/send-alert`
Send emergency email alert to assigned healthcare workers.

**Request Body:**
```json
{
  "message": "Urgent: High blood pressure detected",
  "alert_type": "emergency"
}
```

---

## 📝 Registration & Approvals

### `GET /auth/role-requests`
List all role requests from OAuth flow.

**Response:** `200 OK`
```json
{
  "requests": [
    {
      "id": "uuid",
      "email": "doctor@gmail.com",
      "full_name": "Dr. New Doctor",
      "role_requested": "DOCTOR",
      "degree_cert_url": "https://storage.../cert.pdf",
      "status": "PENDING",
      "created_at": "2026-01-02T10:00:00Z"
    }
  ]
}
```

---

### `POST /auth/role-requests/{id}/approve`
Approve a role request.

**Response:** `200 OK`
```json
{
  "message": "User approved and role assigned",
  "user_id": "uuid",
  "role": "DOCTOR"
}
```

---

### `POST /auth/role-requests/{id}/reject`
Reject a role request.

**Request Body:**
```json
{
  "reason": "Invalid certificate"
}
```

---

### `GET /auth/pending-users`
List OAuth users with no role assigned.

### `POST /auth/pending-users/{id}/assign-role`
Assign role to pending user.

### `POST /auth/pending-users/{id}/reject`
Reject pending user.

---

### `GET /auth/register-requests`
List pending form registrations.

### `POST /auth/register-requests/{id}/decision`
Approve or reject a form registration.

---

## 📊 Analytics

### `GET /analytics/dashboard`
Get basic dashboard analytics.

**Response:** `200 OK`
```json
{
  "total_mothers": 150,
  "risk_distribution": {
    "HIGH": 15,
    "MODERATE": 45,
    "LOW": 90
  },
  "total_assessments": 1200,
  "assessments_this_week": 85
}
```

---

### `GET /dashboard/full`
Combined dashboard endpoint (optimized for frontend).

**Response:** `200 OK`
```json
{
  "analytics": { ... },
  "recent_assessments": [ ... ],
  "high_risk_mothers": [ ... ],
  "upcoming_appointments": [ ... ]
}
```

---

## ❌ Error Handling

All endpoints return standard error responses:

### `400 Bad Request`
```json
{
  "detail": "Invalid request body",
  "errors": [
    { "field": "email", "message": "Invalid email format" }
  ]
}
```

### `401 Unauthorized`
```json
{
  "detail": "Invalid or expired authentication token"
}
```

### `403 Forbidden`
```json
{
  "detail": "You do not have permission to access this resource"
}
```

### `404 Not Found`
```json
{
  "detail": "Resource not found"
}
```

### `500 Internal Server Error`
```json
{
  "detail": "An unexpected error occurred"
}
```

---

## 📚 Additional Resources

- **Interactive API Docs:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

*Last Updated: January 2026*
