import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

from supabase import Client


def _safe_get(d: Dict[str, Any], key: str, default: Any = None):
    try:
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


def build_holistic_context(mother_id: str, supabase: Client, limits: Dict[str, int] | None = None) -> Dict[str, Any]:
    """
    Build a holistic context text for a mother by aggregating:
    - Profile: age, gravida, location, preferred language
    - Recent vitals and lab trends from `health_timeline`
    - TOON summaries and key facts from `context_memory`
    - Recent medical report summaries from `medical_reports`

    Returns a dict with:
    - context_text: str
    - sources: List[str] brief references of items included
    - derived: Dict[str, Any] with computed metrics (e.g., BMI)
    """
    limits = limits or {"timeline": 15, "memories": 25, "reports": 10}

    # Mother profile
    mother_resp = supabase.table("mothers").select("*").eq("id", mother_id).execute()
    mother = mother_resp.data[0] if mother_resp.data else {}

    age = _safe_get(mother, "age")
    gravida = _safe_get(mother, "gravida")
    location = _safe_get(mother, "location")
    preferred_language = _safe_get(mother, "preferred_language", "en")
    height_cm = _safe_get(mother, "height_cm")
    weight_kg = _safe_get(mother, "weight_kg")

    bmi_val, bmi_cat = _compute_bmi(weight_kg or 0, height_cm or 0)

    # Recent timeline vitals (align with schema: order by `event_date`)
    tl_resp = supabase.table("health_timeline").select("*") \
        .eq("mother_id", mother_id).order("event_date", desc=True) \
        .limit(limits["timeline"]).execute()
    timeline = tl_resp.data or []

    # Context memories (TOON summaries, concerns, facts)
    mem_resp = supabase.table("context_memory").select("*") \
        .eq("mother_id", mother_id).order("created_at", desc=True) \
        .limit(limits["memories"]).execute()
    memories = mem_resp.data or []

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

    # Recent reports (use uploaded_at instead of upload_date)
    reports = []
    try:
        rep_resp = supabase.table("medical_reports") \
            .select("*") \
            .eq("mother_id", mother_id) \
            .order("uploaded_at", desc=True) \
            .limit(limits["reports"]).execute()
        reports = rep_resp.data or []
    except Exception as e:
        logger.warning(f"Error fetching reports: {e}")
        reports = []

    # Fetch upcoming appointments (scheduled and in the future)
    upcoming_appt = None
    upcoming_appts = []
    try:
        now_iso = datetime.now().isoformat()
        # Get all upcoming appointments
        appt_resp = supabase.table("appointments").select("*") \
            .eq("mother_id", mother_id) \
            .gte("appointment_date", now_iso) \
            .in_("status", ["scheduled", "pending"]) \
            .order("appointment_date", desc=False) \
            .limit(5).execute()
        if appt_resp.data:
            upcoming_appts = appt_resp.data
            upcoming_appt = appt_resp.data[0]  # Next appointment
        else:
            # Fallback to most recent appointment (even if past)
            last_resp = supabase.table("appointments").select("*") \
                .eq("mother_id", mother_id) \
                .order("appointment_date", desc=True) \
                .limit(1).execute()
            if last_resp.data:
                upcoming_appt = last_resp.data[0]
    except Exception as e:
        logger.warning(f"Error fetching appointments: {e}")
        upcoming_appt = None
        upcoming_appts = []

    # Aggregate vitals (align with timeline schema fields)
    recent_bp = None
    recent_hb = None
    recent_sugar = None
    recent_weight = weight_kg
    for e in timeline:
        try:
            bp_str = e.get("blood_pressure")
            if bp_str and not recent_bp:
                recent_bp = str(bp_str)
        except Exception:
            pass
        if not recent_hb and e.get("hemoglobin") is not None:
            recent_hb = e.get("hemoglobin")
        if e.get("weight") is not None:
            recent_weight = e.get("weight")
        if not recent_sugar:
            # prefer explicit blood_sugar, fallback to sugar_level
            bs = e.get("blood_sugar")
            sl = e.get("sugar_level")
            if bs is not None:
                recent_sugar = bs
            elif sl is not None:
                recent_sugar = sl

    # Derive summary risks (simple illustrative rules)
    derived_risks: List[str] = []
    if age and age >= 35:
        derived_risks.append("Advanced maternal age (>=35)")
    if bmi_cat in {"underweight", "obese"}:
        derived_risks.append(f"BMI category risk: {bmi_cat}")
    if recent_hb and recent_hb < 11.0:
        derived_risks.append("Low hemoglobin — possible anemia risk")
    if recent_bp:
        try:
            sys_dia = str(recent_bp).replace(" ", "").split("/")
            if len(sys_dia) == 2:
                sys = float(sys_dia[0])
                dia = float(sys_dia[1])
                if sys >= 140 or dia >= 90:
                    derived_risks.append("Elevated blood pressure — watch for preeclampsia")
        except Exception:
            pass

    # Compose context text
    lines: List[str] = []
    lines.append("Holistic Context")
    lines.append(f"Mother ID: {mother_id}")
    lines.append(f"Age: {age} | Gravida: {gravida} | Location: {location}")
    lines.append(f"Preferred Language: {preferred_language}")
    lines.append(f"Height(cm): {height_cm} | Weight(kg): {recent_weight}")
    lines.append(f"BMI: {bmi_val} ({bmi_cat})")
    lines.append(f"Recent BP: {recent_bp} | Hb: {recent_hb} | Sugar: {recent_sugar}")
    
    # Add due date if available
    due_date = _safe_get(mother, "due_date")
    if due_date:
        try:
            from datetime import datetime
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            due_str = due_dt.strftime("%B %d, %Y")
            lines.append(f"Due Date: {due_str}")
        except:
            lines.append(f"Due Date: {due_date[:10] if due_date else 'Not set'}")

    # Add appointment details if available
    if upcoming_appt:
        appt_date = upcoming_appt.get("appointment_date")
        appt_type = upcoming_appt.get("appointment_type") or upcoming_appt.get("purpose")
        facility = upcoming_appt.get("facility")
        status = upcoming_appt.get("status")
        try:
            appt_dt = datetime.fromisoformat(appt_date)
            pretty_date = appt_dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pretty_date = appt_date
        lines.append("Next Appointment:")
        lines.append(f"- Date/Time: {pretty_date}")
        if facility:
            lines.append(f"- Facility: {facility}")
        if appt_type:
            lines.append(f"- Type: {appt_type}")
        if status:
            lines.append(f"- Status: {status}")

    if derived_risks:
        lines.append("Derived Risks:")
        for r in derived_risks:
            lines.append(f"- {r}")
    if toon_summaries:
        lines.append("TOON Summaries:")
        for s in toon_summaries[:5]:
            lines.append(f"- {s}")
    if key_concerns:
        lines.append("Key Concerns:")
        for c in key_concerns[:5]:
            lines.append(f"- {c}")

    if reports:
        lines.append("Recent Report Summaries:")
        all_metrics: Dict[str, Any] = {}
        all_concerns: List[str] = []
        all_recommendations: List[str] = []

        def _to_dict(value):
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return {}
            return {}

        def _to_list(value):
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else [value]
                except Exception:
                    return [value]
            if value:
                return [value]
            return []

        for r in reports:
            summary = r.get('analysis_summary', '')
            uploaded_at = r.get('uploaded_at') or r.get('created_at', '')
            date_str = uploaded_at[:10] if uploaded_at else ''
            lines.append(f"- {date_str}: {summary}")

            # Merge health_metrics
            metrics = _to_dict(r.get('health_metrics'))
            for key, val in metrics.items():
                if val not in (None, '', 'null'):
                    all_metrics[key] = val

            # Merge extracted_metrics column
            extracted_metrics = _to_dict(r.get('extracted_metrics'))
            for key, val in extracted_metrics.items():
                if val not in (None, '', 'null'):
                    all_metrics[key] = val

            # Merge analysis_result.extracted_data
            analysis_result = _to_dict(r.get('analysis_result'))
            extracted_data = _to_dict(analysis_result.get('extracted_data')) if analysis_result else {}
            for key, val in extracted_data.items():
                if val not in (None, '', 'null'):
                    all_metrics[key] = val

            # Concerns / recommendations
            all_concerns.extend([c for c in _to_list(r.get('concerns')) if c])
            all_recommendations.extend([rec for rec in _to_list(r.get('recommendations')) if rec])

        if all_metrics:
            lines.append("Combined Metrics From Reports:")
            for key, val in all_metrics.items():
                lines.append(f"- {key.replace('_', ' ').title()}: {val}")

        if all_concerns:
            lines.append("Report Concerns:")
            for concern in sorted(set(all_concerns)):
                lines.append(f"- {concern}")

        if all_recommendations:
            lines.append("Report Recommendations:")
            for rec in sorted(set(all_recommendations)):
                lines.append(f"- {rec}")

    if key_facts:
        lines.append("Other Known Facts:")
        for f in key_facts[:5]:
            lines.append(f"- {f}")

    sources: List[str] = []
    sources.append("mothers.profile")
    sources.append("health_timeline.latest")
    if upcoming_appt:
        sources.append("appointments.next")
    if toon_summaries:
        sources.append("context_memory.toon")
    if key_concerns:
        sources.append("context_memory.concerns")
    if key_facts:
        sources.append("context_memory.facts")
    if reports:
        sources.append("medical_reports.summaries")
        sources.append("medical_reports.metrics")

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
    }