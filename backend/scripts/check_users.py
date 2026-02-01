"""Check all users and their roles"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("All users in user_profiles:")
all_users = c.table("user_profiles").select("*").execute()
for u in all_users.data:
    role = u.get('role')
    print(f"  Email: {u['email']}")
    print(f"  Role: {repr(role)} (type: {type(role).__name__})")
    print(f"  Role is None: {role is None}")
    print(f"  Role == 'null': {role == 'null'}")
    print(f"  ---")
