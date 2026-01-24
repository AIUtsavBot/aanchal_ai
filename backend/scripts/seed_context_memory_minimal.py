import os
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
m = db.table("mothers").select("id, phone").eq("phone", PHONE).execute().data
if not m:
    raise SystemExit("Mother not found; run main seed first.")
mother_id = m[0]["id"]

items = [
    {"mother_id": mother_id, "memory_key": "next_consultation", "memory_value": (datetime.now()+timedelta(days=3)).isoformat()},
    {"mother_id": mother_id, "memory_key": "medications", "memory_value": "IFA OD; Calcium OD"}
]
res = db.table("context_memory").insert(items).execute()
print("Inserted context memories:", len(res.data))