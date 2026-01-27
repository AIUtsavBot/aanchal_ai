
import os
import asyncio
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker

# Try to import supabase
try:
    from supabase import create_client
except ImportError:
    print("Please install supabase: pip install supabase")
    exit(1)

load_dotenv()
fake = Faker('en_IN')  # Use Indian locale for names

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    print("SUPABASE_URL not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def seed_data():
    print("🌱 Starting Demo Data Seeding...")
    
    # 1. Create Dummy Users (if not exist)
    # Note: Creating auth users via script is tricky without service role, 
    # so we will focus on 'public' tables or assume users exist.
    # We will create Mothers directly.

    # 2. Seed Mothers
    mothers = []
    print("... Seeding Mothers")
    for _ in range(5):
        m = {
            "name": fake.name_female(),
            "age": random.randint(19, 35),
            "phone_number": fake.phone_number(),
            "blood_type": random.choice(["A+", "B+", "O+", "AB+", "O-"]),
            "due_date": (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat(),
            "pregnancy_risk_level": random.choice(["LOW", "LOW", "MODERATE", "HIGH"]),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
            "assigned_area": random.choice(["North Zone", "South Zone", "East Zone"]),
            "language_preference": "hi",
            "medical_history": {"diabetes": random.choice([True, False]), "hypertension": False}
        }
        res = supabase.table("mothers").insert(m).execute()
        if res.data:
            mothers.extend(res.data)
            
    print(f"✓ Created {len(mothers)} mothers")
    
    # 3. Seed Risk Assessments & Vitals
    print("... Seeding Health Records")
    for mother in mothers:
        mid = mother['id']
        
        # Create 3-5 assessments per mother
        for i in range(random.randint(3, 5)):
            date_offset = timedelta(days=random.randint(0, 60))
            assess_date = (datetime.now() - date_offset).isoformat()
            
            # Simulate a trend (e.g. rising BP for some)
            sys_bp = 110 + (i * 5) if mother['pregnancy_risk_level'] == 'HIGH' else random.randint(110, 125)
            dia_bp = 70 + (i * 3) if mother['pregnancy_risk_level'] == 'HIGH' else random.randint(70, 80)
            
            assessment = {
                "mother_id": mid,
                "systolic_bp": sys_bp,
                "diastolic_bp": dia_bp,
                "weight_kg": 55 + (i * 0.5),
                "hemoglobin": random.uniform(9.0, 12.0),
                "fetal_heart_rate": random.randint(120, 160),
                "symptoms": ["headache"] if sys_bp > 130 else [],
                "created_at": assess_date
            }
            supabase.table("risk_assessments").insert(assessment).execute()
            
            # Seed Health Metric
            metric = {
                "mother_id": mid,
                "metric_type": "weight",
                "value": assessment["weight_kg"],
                "measured_at": assess_date
            }
            supabase.table("health_metrics").insert(metric).execute()

    print("✓ Created Risk Assessments & Metrics")
    
    # 4. Seed Children & Vaccinations (for some mothers who already delivered)
    print("... Seeding Children")
    # Fetch existing mothers just in case
    # For demo, let's create a couple of delivered mothers/children separately or just add children to existing
    for i in range(2):
        child = {
            "name": fake.first_name(),
            "mother_id": mothers[i]['id'] if mothers else None, # Link to first few mothers
            "date_of_birth": (datetime.now() - timedelta(days=random.randint(10, 300))).isoformat(),
            "gender": random.choice(["Male", "Female"]),
            "weight_kg": random.uniform(2.5, 8.0),
            "blood_type": random.choice(["A+", "O+"])
        }
        res = supabase.table("children").insert(child).execute()
        
        if res.data:
            cid = res.data[0]['id']
            # Seed Vaccinations
            vacs = [
                {"child_id": cid, "vaccine_name": "BCG", "status": "COMPLETED", "administered_date": child['date_of_birth']},
                {"child_id": cid, "vaccine_name": "OPV-0", "status": "COMPLETED", "administered_date": child['date_of_birth']},
                {"child_id": cid, "vaccine_name": "Pentavalent-1", "status": "PENDING", "due_date": (datetime.now() + timedelta(days=30)).isoformat()}
            ]
            supabase.table("vaccinations").insert(vacs).execute()

    print("✓ Created Children & Vaccinations")
    print("✨ Seeding Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
