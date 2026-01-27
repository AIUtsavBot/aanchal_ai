
import os
import json
import asyncio
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials missing")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BACKUP_DIR = "backups"

CRITICAL_TABLES = [
    "mothers",
    "children",
    "vaccinations",
    "growth_records",
    "risk_assessments",
    "users",
    "appointments"
]

async def backup_table(table_name):
    print(f"Backing up {table_name}...")
    try:
        # Fetch all rows (pagination might be needed for huge DBs, but simple for now)
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        return data
    except Exception as e:
        print(f"Failed to backup {table_name}: {e}")
        return None

async def main():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_path)
    
    print(f"Starting backup at {timestamp} to {backup_path}")
    
    tasks = [backup_table(table) for table in CRITICAL_TABLES]
    results = await asyncio.gather(*tasks)
    
    summary = {"timestamp": timestamp, "tables": {}}
    
    for table, data in zip(CRITICAL_TABLES, results):
        if data is not None:
            file_path = os.path.join(backup_path, f"{table}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
            summary["tables"][table] = len(data)
            print(f"✓ {table}: {len(data)} records")
        else:
            summary["tables"][table] = "FAILED"
            print(f"✗ {table}: FAILED")
            
    # Save summary
    with open(os.path.join(backup_path, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        
    print("Backup completed.")

if __name__ == "__main__":
    asyncio.run(main())
