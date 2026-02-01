"""
Reset password for a user
Usage: python reset_password.py email@example.com newpassword123
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

if len(sys.argv) < 3:
    print("Usage: python reset_password.py <email> <new_password>")
    print("Example: python reset_password.py aiml.utssav@gmail.com MyNewPass123")
    sys.exit(1)

email = sys.argv[1]
new_password = sys.argv[2]

if len(new_password) < 6:
    print("Error: Password must be at least 6 characters")
    sys.exit(1)

c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Find the user
users = c.auth.admin.list_users()
user = None
for u in users:
    if u.email and u.email.lower() == email.lower():
        user = u
        break

if not user:
    print(f"Error: User with email {email} not found")
    sys.exit(1)

print(f"Found user: {user.email} (ID: {user.id})")

# Update the password
try:
    c.auth.admin.update_user_by_id(user.id, {"password": new_password})
    print(f"[OK] Password updated successfully!")
    print(f"You can now login with:")
    print(f"  Email: {email}")
    print(f"  Password: {new_password}")
except Exception as e:
    print(f"[FAIL] Failed to update password: {e}")
