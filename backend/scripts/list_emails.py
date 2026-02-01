import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

users = c.auth.admin.list_users()
print("All users in Supabase Auth:")
for u in users:
    print(f"  {u.email}")
