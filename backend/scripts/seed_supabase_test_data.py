"""
Seed Supabase with realistic test data for MatruRaksha AI.

What it creates:
- Mother profile (if not exists) and returns mother_id
- Upcoming appointments (next consultation timings)
- Health timeline events (consultations, prescriptions, lab assessments)
- Medical report analyses
- Health metrics (BP, Hb, glucose, weight)
- Context memories for quick agent context
- A few conversation rows

Usage:
  set SUPABASE_URL and SUPABASE_KEY in environment
  python backend/scripts/seed_supabase_test_data.py --mother-name "Priya Sharma"

Optional args:
  --mother-phone "9990001111" --language "en" --chat-id "123456789"

"""
import os
import argparse
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# ---- Env & Client ----
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_mother(name: str, phone: str, language: str, chat_id: Optional[str]) -> int:
    existing = db.table("mothers").select("id, phone").eq("phone", phone).execute().data
    if existing:
        return existing[0]["id"]
    payload = {
        "name": name,
        "phone": phone,
        "age": 28,
        "gravida": 2,
        "parity": 1,
        "bmi": 23.5,
        "location": "Dharavi, Mumbai",
        "preferred_language": language,
        "telegram_chat_id": chat_id,
        "created_at": datetime.now().isoformat()
    }
    res = db.table("mothers").insert(payload).execute()
    return res.data[0]["id"]


def add_appointments(mother_id: int, chat_id: Optional[str]) -> None:
    base = datetime.now() + timedelta(days=3)
    items = [
        {
            "mother_id": mother_id,
            "appointment_type": "ANC Consultation",
            "appointment_date": (base).isoformat(),
            "notes": "Routine ANC check with BP, Hb.",
            "status": "scheduled"
        },
        {
            "mother_id": mother_id,
            "appointment_type": "Ultrasound",
            "appointment_date": (base + timedelta(days=14)).isoformat(),
            "notes": "Growth scan.",
            "status": "scheduled"
        },
        {
            "mother_id": mother_id,
            "appointment_type": "Diabetes Review",
            "appointment_date": (base + timedelta(days=28)).isoformat(),
            "notes": "Review fasting glucose and diet adherence.",
            "status": "scheduled"
        }
    ]
    try:
        db.table("appointments").insert(items).execute()
    except Exception as e:
        print("Appointments seed skipped:", e)


def add_timeline(mother_id: int) -> None:
    today = datetime.now().date()
    events = [
        {
            "mother_id": mother_id,
            "event_date": today.isoformat(),
            "event_type": "doctor_consultation",
            "event_data": json.dumps({
                "facility": "Community Health Center",
                "doctor": "Dr. Mehta",
                "reason": "Routine ANC",
            }),
            "blood_pressure": "122/78",
            "hemoglobin": 11.8,
            "sugar_level": 92.0,
            "weight": 62.4,
            "summary": "Routine ANC visit; vitals stable, mild anemia acknowledged.",
            "concerns": json.dumps(["Mild anemia"])
        },
        {
            "mother_id": mother_id,
            "event_date": (today + timedelta(days=1)).isoformat(),
            "event_type": "prescription",
            "event_data": json.dumps({
                "medications": [
                    {"name": "Iron + Folic Acid", "dosage": "60 mg", "frequency": "OD"},
                    {"name": "Calcium + Vitamin D3", "dosage": "500 mg", "frequency": "OD"}
                ],
                "advice": "Hydration, balanced diet with leafy greens."
            }),
            "summary": "Doctor prescribed IFA and Calcium; lifestyle advice given.",
            "concerns": json.dumps([])
        },
        {
            "mother_id": mother_id,
            "event_date": (today + timedelta(days=2)).isoformat(),
            "event_type": "lab_result_summary",
            "event_data": json.dumps({
                "lab": "CBC",
                "hemoglobin": 11.6,
                "platelets": 250000,
                "wbc": 7200
            }),
            "summary": "CBC shows mild anemia; other counts normal.",
            "concerns": json.dumps(["Hb slightly low"])
        }
    ]
    db.table("health_timeline").insert(events).execute()


def add_medical_reports(mother_id: int) -> None:
    reports = [
        {
            "mother_id": mother_id,
            "filename": "cbc_report_2025-11-20.pdf",
            "upload_date": datetime.now().isoformat(),
            "analysis_summary": "CBC indicates mild iron-deficiency anemia; recommend IFA.",
            "health_metrics": json.dumps({"hemoglobin": 11.6, "wbc": 7200, "platelets": 250000}),
            "concerns": json.dumps(["Hb below optimal range for pregnancy"]),
            "recommendations": json.dumps(["Continue IFA", "Diet rich in iron and vitamin C"]),
            "processed": True
        },
        {
            "mother_id": mother_id,
            "filename": "bp_check_2025-11-21.jpg",
            "upload_date": datetime.now().isoformat(),
            "analysis_summary": "Blood pressure within normal range; continue monitoring.",
            "health_metrics": json.dumps({"blood_pressure": "122/78"}),
            "concerns": json.dumps([]),
            "recommendations": json.dumps(["Maintain low-salt diet", "Regular physical activity"]),
            "processed": True
        }
    ]
    db.table("medical_reports").insert(reports).execute()


def add_health_metrics(mother_id: int) -> None:
    metrics = [
        {
            "mother_id": mother_id,
            "weight_kg": 62.4,
            "blood_pressure_systolic": 122,
            "blood_pressure_diastolic": 78,
            "hemoglobin": 11.8,
            "blood_sugar": 92.0,
            "measured_at": datetime.now().isoformat(),
            "notes": "Routine ANC vitals"
        },
        {
            "mother_id": mother_id,
            "weight_kg": 62.8,
            "blood_pressure_systolic": 124,
            "blood_pressure_diastolic": 80,
            "hemoglobin": 11.6,
            "blood_sugar": 95.0,
            "measured_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "notes": "Follow-up vitals"
        }
    ]
    db.table("health_metrics").insert(metrics).execute()


def add_context_memory(mother_id: int) -> None:
    memories = [
        {"mother_id": mother_id, "memory_key": "next_consultation", "memory_value": (datetime.now()+timedelta(days=3)).isoformat(), "memory_type": "schedule", "source": "system"},
        {"mother_id": mother_id, "memory_key": "diet_advice", "memory_value": "Leafy greens + vitamin C for iron absorption", "memory_type": "advice", "source": "doctor"},
        {"mother_id": mother_id, "memory_key": "latest_bp", "memory_value": "122/78", "memory_type": "health_metric", "source": "report"},
        {"mother_id": mother_id, "memory_key": "medications", "memory_value": "IFA OD; Calcium OD", "memory_type": "prescription", "source": "doctor"}
    ]
    db.table("context_memory").insert(memories).execute()


def add_conversations(mother_id: int, chat_id: Optional[str]) -> None:
    convos = [
        {
            "mother_id": mother_id,
            "message_role": "user",
            "message_content": "When is my next consultation?",
            "context_used": json.dumps(["health_timeline", "context_memory"])
        },
        {
            "mother_id": mother_id,
            "message_role": "assistant",
            "message_content": "Your next ANC consultation is scheduled in 3 days at Community Health Center.",
            "agent_response": json.dumps({"source": "seed"})
        },
        {
            "mother_id": mother_id,
            "message_role": "user",
            "message_content": "What medicines did the doctor prescribe?",
            "context_used": json.dumps(["health_timeline", "medical_reports"])
        },
        {
            "mother_id": mother_id,
            "message_role": "assistant",
            "message_content": "Iron+Folic Acid once daily and Calcium+Vitamin D3 once daily.",
            "agent_response": json.dumps({"source": "seed"})
        }
    ]
    db.table("conversations").insert(convos).execute()


def seed_all(name: str, phone: str, language: str, chat_id: Optional[str]) -> Dict[str, Any]:
    mother_id = upsert_mother(name, phone, language, chat_id)
    add_appointments(mother_id, chat_id)
    add_timeline(mother_id)
    add_medical_reports(mother_id)
    add_health_metrics(mother_id)
    add_context_memory(mother_id)
    add_conversations(mother_id, chat_id)
    return {"mother_id": mother_id}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Supabase with MatruRaksha test data")
    parser.add_argument("--mother-name", default="Priya Sharma")
    parser.add_argument("--mother-phone", default="9990001111")
    parser.add_argument("--language", default="en")
    parser.add_argument("--chat-id", default="123456789")
    args = parser.parse_args()

    result = seed_all(args.mother_name, args.mother_phone, args.language, args.chat_id)
    print("Seed completed:", result)