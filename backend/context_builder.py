import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional
from functools import lru_cache
from supabase import Client

logger = logging.getLogger(__name__)

# Simple in-memory cache for profiles (ID -> (data, timestamp))
_profile_cache: Dict[str, Tuple[Dict, datetime]] = {}
CACHE_TTL = 300  # 5 minutes

def _safe_get(d: Dict[str, Any], key: str, default: Any = None):
    try:
        if not d: return default
        return d.get(key, default)
    except Exception:
        return default

def _compute_bmi(weight: float, height_cm: float) -> Tuple[float, str]:
    try:
        if not weight or not height_cm:
            return (0.0, "unknown")
        h_m = height_cm / 100.0
        bmi = round(weight / (h_m * h_m), 2)
        if bmi < 18.5:
            cat = "underweight"
        elif bmi < 25:
            cat = "normal"
        elif bmi < 30:
            cat = "overweight"
        else:
            cat = "obese"
        return (bmi, cat)
    except Exception:
        return (0.0, "unknown")

# --- Async Helper Functions (Run in Thread Pool) ---

def _fetch_profile_sync(mother_id: str, supabase: Client) -> Dict[str, Any]:
    # Check cache
    if mother_id in _profile_cache:
        data, timestamp = _profile_cache[mother_id]
        if (datetime.now() - timestamp).seconds < CACHE_TTL:
            return data
            
    resp = supabase.table("mothers").select("*").eq("id", mother_id).execute()
    data = resp.data[0] if resp.data else {}
    
    # Update cache
    if data:
        _profile_cache[mother_id] = (data, datetime.now())
        
    return data

def _fetch_timeline_sync(mother_id: str, supabase: Client, limit: int) -> List[Dict]:
    resp = supabase.table("health_timeline").select("*") \
        .eq("mother_id", mother_id).order("event_date", desc=True) \
        .limit(limit).execute()
    return resp.data or []

def _fetch_memories_sync(mother_id: str, supabase: Client, limit: int) -> List[Dict]:
    resp = supabase.table("context_memory").select("*") \
        .eq("mother_id", mother_id).order("created_at", desc=True) \
        .limit(limit).execute()
    return resp.data or []

def _fetch_reports_sync(mother_id: str, supabase: Client, limit: int) -> List[Dict]:
    try:
        resp = supabase.table("medical_reports") \
            .select("*") \
            .eq("mother_id", mother_id) \
            .order("uploaded_at", desc=True) \
            .limit(limit).execute()
        return resp.data or []
    except Exception:
        return []

def _fetch_appointments_sync(mother_id: str, supabase: Client) -> List[Dict]:
    try:
        now_iso = datetime.now().isoformat()
        resp = supabase.table("appointments").select("*") \
            .eq("mother_id", mother_id) \
            .gte("appointment_date", now_iso) \
            .in_("status", ["scheduled", "pending"]) \
            .order("appointment_date", desc=False) \
            .limit(5).execute()
        return resp.data or []
    except Exception:
        return []

def _fetch_risks_sync(mother_id: str, supabase: Client) -> List[Dict]:
    try:
        resp = supabase.table("risk_assessments").select("*") \
            .eq("mother_id", mother_id).order("created_at", desc=True).limit(3).execute()
        return resp.data or []
    except Exception:
        return []

# --- Main Async Builder ---

async def build_holistic_context_async(mother_id: str, supabase: Client, limits: Dict[str, int] | None = None) -> Dict[str, Any]:
    """
    Async + Parallelized version of context builder.
    """
    limits = limits or {"timeline": 15, "memories": 25, "reports": 10}
    
    # Launch parallel tasks using threads for blocking IO
    start_time = datetime.now()
    
    tasks = [
        asyncio.to_thread(_fetch_profile_sync, mother_id, supabase),
        asyncio.to_thread(_fetch_timeline_sync, mother_id, supabase, limits["timeline"]),
        asyncio.to_thread(_fetch_memories_sync, mother_id, supabase, limits["memories"]),
        asyncio.to_thread(_fetch_reports_sync, mother_id, supabase, limits["reports"]),
        asyncio.to_thread(_fetch_appointments_sync, mother_id, supabase),
        asyncio.to_thread(_fetch_risks_sync, mother_id, supabase)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Unpack results (handling exceptions gracefully)
    mother = results[0] if not isinstance(results[0], Exception) else {}
    timeline = results[1] if not isinstance(results[1], Exception) else []
    memories = results[2] if not isinstance(results[2], Exception) else []
    reports = results[3] if not isinstance(results[3], Exception) else []
    upcoming_appts = results[4] if not isinstance(results[4], Exception) else []
    recent_risks = results[5] if not isinstance(results[5], Exception) else []
    
    upcoming_appt = upcoming_appts[0] if upcoming_appts else None
    
    # --- Processing Logic (CPU bound, fast) ---
    
    age = _safe_get(mother, "age")
    gravida = _safe_get(mother, "gravida")
    location = _safe_get(mother, "location")
    preferred_language = _safe_get(mother, "preferred_language", "en")
    height_cm = _safe_get(mother, "height_cm")
    weight_kg = _safe_get(mother, "weight_kg")
    
    bmi_val, bmi_cat = _compute_bmi(weight_kg or 0, height_cm or 0)
    
    toon_summaries: List[str] = []
    key_concerns: List[str] = []
    key_facts: List[str] = []
    
    for m in memories:
        key = _safe_get(m, "memory_key", "")
        val = _safe_get(m, "memory_value", "")
        typ = _safe_get(m, "memory_type", "")
        if "toon" in key.lower() or typ == "toon":
            toon_summaries.append(str(val))
        elif typ == "concern":
            key_concerns.append(str(val))
        else:
            key_facts.append(f"{key}: {val}")
            
    # Aggregate vitals from timeline
    recent_bp = None
    recent_hb = None
    recent_sugar = None
    recent_weight = weight_kg
    
    for e in timeline:
        try:
            if not recent_bp and e.get("blood_pressure"):
                recent_bp = str(e.get("blood_pressure"))
        except: pass
        if not recent_hb: recent_hb = e.get("hemoglobin")
        if not recent_weight: recent_weight = e.get("weight")
        if not recent_sugar:
            recent_sugar = e.get("blood_sugar") or e.get("sugar_level")
            
    # Derive Risks
    derived_risks: List[str] = []
    if age and age >= 35: derived_risks.append("Advanced maternal age (>=35)")
    if bmi_cat in {"underweight", "obese"}: derived_risks.append(f"BMI risk: {bmi_cat}")
    
    # Pregnancy History (for Postnatal)
    pregnancy_history: List[str] = []
    is_postnatal = mother.get('active_system') == 'santanraksha' or mother.get('delivery_status') in ['delivered', 'postnatal']
    
    if is_postnatal and timeline:
        keywords = {'preeclampsia', 'gdm', 'diabetes', 'anemia', 'hemorrhage', 'complication'}
        for event in timeline: # using timeline we already fetched (might need deeper fetch if limit is small, but stick to this for perf)
            txt = (str(event.get('summary', '')) + str(event.get('concerns', ''))).lower()
            if any(k in txt for k in keywords):
                pregnancy_history.append(f"{event.get('event_date')}: {event.get('summary')}")

    # Build Text Context
    lines: List[str] = []
    lines.append("Holistic Context")
    lines.append(f"Profile: {mother_id} | Age: {age} | Gravida: {gravida}")
    lines.append(f"Lang: {preferred_language} | Loc: {location}")
    lines.append(f"Biometrics: Ht {height_cm}cm | Wt {recent_weight}kg | BMI {bmi_val} ({bmi_cat})")
    lines.append(f"Vitals: BP {recent_bp} | Hb {recent_hb} | Sugar {recent_sugar}")
    
    if is_postnatal:
        lines.append(f"Status: Postnatal/Delivered")
    else:
        due = mother.get("due_date")
        if due: lines.append(f"Due Date: {due[:10]}")

    if upcoming_appt:
        dt = upcoming_appt.get("appointment_date", "")[:16].replace("T", " ")
        lines.append(f"Next Appt: {dt} ({upcoming_appt.get('appointment_type')})")
        
    if derived_risks:
        lines.append("Risks: " + ", ".join(derived_risks))
        
    if recent_risks:
        lines.append("Recent Assessments:")
        for r in recent_risks:
            risk_label = r.get('risk_level', '').upper()
            lines.append(f"- {r.get('created_at', '')[:10]}: {risk_label}")

    if key_concerns:
        lines.append("Concerns:")
        for c in key_concerns[:3]: lines.append(f"- {c}")
        
    if reports:
        lines.append("Latest Reports:")
        for r in reports[:3]:
            lines.append(f"- {r.get('uploaded_at','')[:10]}: {r.get('analysis_summary','')}")

    # Sources
    sources = ["profile", "timeline", "memories", "reports", "appointments"]
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"⚡ Context built in {elapsed:.2f}s for {mother_id}")

    return {
        "context_text": "\n".join(lines),
        "sources": sources,
        "derived": {
            "bmi": bmi_val,
            "bmi_category": bmi_cat,
            "recent_bp": recent_bp,
            "recent_hb": recent_hb,
            "recent_sugar": recent_sugar,
        },
        # Return raw data for agents that want it structured
        "raw_data": {
            "profile": mother,
            "timeline": timeline,
            "appointments": upcoming_appts,
            "risks": recent_risks
        }
    }

# Sync wrapper for backward compatibility if absolutely needed
def build_holistic_context_sync(mother_id: str, supabase: Client):
    return asyncio.run(build_holistic_context_async(mother_id, supabase))