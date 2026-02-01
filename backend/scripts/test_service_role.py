"""
Quick test script to verify Supabase service role key is working
Run: python test_service_role.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("🔍 Supabase Service Role Key Test")
print("=" * 60)

# Check if keys are set
print(f"\n1. SUPABASE_URL set: {bool(SUPABASE_URL)}")
print(f"2. SUPABASE_KEY (anon) set: {bool(SUPABASE_KEY)}")
print(f"3. SUPABASE_SERVICE_ROLE_KEY set: {bool(SUPABASE_SERVICE_ROLE_KEY)}")

if not SUPABASE_SERVICE_ROLE_KEY:
    print("\n❌ ERROR: SUPABASE_SERVICE_ROLE_KEY is not set!")
    print("   Go to Supabase Dashboard > Settings > API > service_role key")
    exit(1)

# Check key format
if SUPABASE_SERVICE_ROLE_KEY.startswith("eyJ"):
    print(f"4. Service role key format: ✅ Valid JWT format")
    print(f"   Key length: {len(SUPABASE_SERVICE_ROLE_KEY)} characters")
else:
    print(f"4. Service role key format: ❌ Invalid (should start with 'eyJ')")
    exit(1)

# Check if it's different from anon key
if SUPABASE_SERVICE_ROLE_KEY == SUPABASE_KEY:
    print("\n⚠️  WARNING: Service role key is the same as anon key!")
    print("   You need the service_role key, not the anon key")
    exit(1)
else:
    print("5. Service role key is different from anon key: ✅")

# Test the admin API
print("\n📡 Testing Supabase Admin API...")
try:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Try to list users (this requires service role permissions)
    users = supabase_admin.auth.admin.list_users()
    print(f"6. Admin API access: ✅ Working!")
    print(f"   Found {len(users)} existing users in auth.users")
    
    # Show existing users (just email and role)
    if users:
        print("\n   Existing users:")
        for u in users[:5]:  # Show first 5
            email = u.email or "no-email"
            role = u.user_metadata.get("role", "unknown") if u.user_metadata else "unknown"
            print(f"   - {email} ({role})")
        if len(users) > 5:
            print(f"   ... and {len(users) - 5} more")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Your service role key is working correctly!")
    print("   You can now approve registration requests.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Admin API test failed: {e}")
    print("\n   This usually means:")
    print("   - The service role key is invalid or expired")
    print("   - You're using the anon key instead of service_role key")
    print("\n   Fix: Copy the correct service_role key from:")
    print("   Supabase Dashboard > Settings > API > service_role (secret)")
