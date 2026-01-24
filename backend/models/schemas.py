# FILE: backend/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== MOTHER SCHEMA ====================
class Mother(BaseModel):
    name: str = Field(..., min_length=1, description="Mother's full name")
    phone: str = Field(..., min_length=10, description="Phone number")
    age: int = Field(..., ge=15, le=50, description="Age in years")
    gravida: int = Field(..., ge=1, description="Number of pregnancies")
    parity: int = Field(..., ge=0, description="Number of deliveries")
    bmi: float = Field(..., ge=10, le=50, description="Body Mass Index")
    location: str = Field(..., min_length=1, description="Location/Area")
    preferred_language: str = Field(default="en", description="Language preference: en, mr, hi")
    telegram_chat_id: Optional[str] = Field(default=None, description="Optional Telegram Chat ID")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Priya Sharma",
                "phone": "9876543210",
                "age": 28,
                "gravida": 2,
                "parity": 1,
                "bmi": 23.5,
                "location": "Dharavi, Mumbai",
                "preferred_language": "mr",
                "telegram_chat_id": "123456789"
            }
        }


class MotherId(BaseModel):
    id: str


# ==================== VISIT SCHEMA ====================
class Visit(BaseModel):
    mother_id: str
    visit_date: Optional[datetime] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    blood_glucose: Optional[float] = None
    hemoglobin: Optional[float] = None
    weight: Optional[float] = None
    notes: Optional[str] = None


# ==================== RISK ASSESSMENT SCHEMA ====================
class RiskAssessment(BaseModel):
    mother_id: str
    systolic_bp: Optional[int] = Field(None, ge=60, le=200)
    diastolic_bp: Optional[int] = Field(None, ge=30, le=130)
    heart_rate: Optional[int] = Field(None, ge=40, le=200)
    blood_glucose: Optional[float] = Field(None, ge=50, le=500)
    hemoglobin: Optional[float] = Field(None, ge=5, le=20)
    proteinuria: int = Field(default=0, ge=0, le=1)
    edema: int = Field(default=0, ge=0, le=1)
    headache: int = Field(default=0, ge=0, le=1)
    vision_changes: int = Field(default=0, ge=0, le=1)
    epigastric_pain: int = Field(default=0, ge=0, le=1)
    vaginal_bleeding: int = Field(default=0, ge=0, le=1)
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "mother_id": "uuid-here",
                "systolic_bp": 140,
                "diastolic_bp": 90,
                "heart_rate": 88,
                "blood_glucose": 120,
                "hemoglobin": 11.5,
                "proteinuria": 1,
                "edema": 0,
                "headache": 1,
                "vision_changes": 0,
                "epigastric_pain": 0,
                "vaginal_bleeding": 0,
                "notes": "Patient reports headache"
            }
        }


# ==================== APPOINTMENT SCHEMA ====================
class Appointment(BaseModel):
    mother_id: str
    facility: str
    appointment_date: str  # "YYYY-MM-DD"
    appointment_time: str  # "HH:MM AM/PM"
    purpose: Optional[str] = None
    notes: Optional[str] = None


# ==================== MEDICATION SCHEMA ====================
class Medication(BaseModel):
    mother_id: str
    medicine_name: str
    dosage: str
    frequency: str
    start_date: str
    end_date: Optional[str] = None
    notes: Optional[str] = None


# ==================== EMERGENCY INCIDENT SCHEMA ====================
class EmergencyIncident(BaseModel):
    mother_id: str
    symptoms: list
    severity: str  # "low", "medium", "high", "critical"
    location: str
    nearest_facility: Optional[str] = None
    contacted_at: Optional[datetime] = None
    notes: Optional[str] = None


# ==================== RESPONSE SCHEMAS ====================
class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: Optional[str] = None


class RiskScoreResponse(BaseModel):
    risk_score: float
    status: str
    risk_level: str
    recommendations: list
    emergency_alert: bool
    timestamp: datetime


class AnalyticsResponse(BaseModel):
    total_mothers: int
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int
    assessments_done: int
    last_updated: datetime