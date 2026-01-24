import os
import json
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

PHONE = os.getenv("SEED_PHONE", "9990001111")
mother = db.table("mothers").select("id, phone").eq("phone", PHONE).execute().data
if not mother:
    raise SystemExit(f"No mother found with phone {PHONE}. Run main seed first.")
mother_id = mother[0]["id"]

today = datetime.now().date()
events = [
    {
        "mother_id": mother_id,
        "event_date": today.isoformat(),
        "event_type": "doctor_consultation"
    },
    {
        "mother_id": mother_id,
        "event_date": (today + timedelta(days=1)).isoformat(),
        "event_type": "prescription"
    }
]

res = db.table("health_timeline").insert(events).execute()
print("Inserted timeline events:", len(res.data))