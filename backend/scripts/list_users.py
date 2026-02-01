import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
users = c.auth.admin.list_users()

print("=" * 50)
print("Users in Supabase Auth:")
print("=" * 50)
for u in users:
    email = u.email or "no-email"
    role = u.user_metadata.get("role", "N/A") if u.user_metadata else "N/A"
    print(f"  - {email} (role: {role})")

print("\n" + "=" * 50)
print("Pending registration requests:")
print("=" * 50)
reqs = c.table("registration_requests").select("id,email,role_requested,status").execute()
for r in reqs.data:
    print(f"  - ID {r['id']}: {r['email']} ({r['role_requested']}) - {r['status']}")
