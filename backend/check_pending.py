"""Check pending users in user_profiles"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("=" * 50)
print("All users in user_profiles:")
print("=" * 50)

all_users = c.table("user_profiles").select("id, email, full_name, role, created_at").execute()
for u in all_users.data:
    role = u.get('role')
    role_str = f"'{role}'" if role else 'NULL'
    print(f"  {u['email']} - role: {role_str}")

print("\n" + "=" * 50)
print("Testing NULL query:")
print("=" * 50)

# Try different ways to query NULL
try:
    result1 = c.table("user_profiles").select("*").is_("role", "null").execute()
    print(f"is_('role', 'null'): {len(result1.data)} users")
    for u in result1.data:
        print(f"  - {u['email']}")
except Exception as e:
    print(f"is_('role', 'null') error: {e}")

try:
    # Also try filter for NULL
    result2 = c.table("user_profiles").select("*").filter("role", "is", "null").execute()
    print(f"filter('role', 'is', 'null'): {len(result2.data)} users")
    for u in result2.data:
        print(f"  - {u['email']}")
except Exception as e:
    print(f"filter error: {e}")
