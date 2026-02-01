"""
Fix script: Create users for approved registration requests that failed to create user
"""
import os
import secrets
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("=" * 60)
print("[FIX] Fixing Approved Requests Without Created Users")
print("=" * 60)

# Get all approved requests
approved = c.table("registration_requests").select("*").eq("status", "APPROVED").execute()
auth_users = c.auth.admin.list_users()
auth_emails = {u.email.lower() for u in auth_users if u.email}

print(f"\nFound {len(approved.data)} approved requests")
print(f"Found {len(auth_emails)} existing users in auth")

fixed = 0
for req in approved.data:
    email = req.get("email", "").lower()
    if email not in auth_emails:
        print(f"\n[!] User not created for: {email}")
        
        # We'll need to use a temp password since we can't decrypt the old one
        temp_password = secrets.token_urlsafe(12)
        
        try:
            created = c.auth.admin.create_user({
                "email": email,
                "password": temp_password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": req.get("full_name"),
                    "role": req.get("role_requested"),
                    "phone": req.get("phone"),
                    "assigned_area": req.get("assigned_area")
                }
            })
            user_id = created.user.id
            print(f"   [OK] Created user: {user_id}")
            print(f"   Email: {email}")
            print(f"   TEMPORARY PASSWORD: {temp_password}")
            print(f"   [!] User must change this password!")
            
            # Update user_profiles
            c.table("user_profiles").upsert({
                "id": user_id,
                "email": email,
                "full_name": req.get("full_name"),
                "role": req.get("role_requested"),
                "phone": req.get("phone"),
                "assigned_area": req.get("assigned_area"),
                "is_active": True
            }).execute()
            print(f"   [OK] Updated user_profiles")
            
            # Create role-specific entry
            role = req.get("role_requested")
            if role == "DOCTOR":
                c.table("doctors").upsert({
                    "user_profile_id": user_id,
                    "name": req.get("full_name"),
                    "email": email,
                    "phone": req.get("phone") or "",
                    "assigned_area": req.get("assigned_area") or "",
                    "is_active": True
                }).execute()
                print(f"   [OK] Created doctor entry")
            elif role == "ASHA_WORKER":
                c.table("asha_workers").upsert({
                    "user_profile_id": user_id,
                    "name": req.get("full_name"),
                    "email": email,
                    "phone": req.get("phone") or "",
                    "assigned_area": req.get("assigned_area") or "",
                    "is_active": True
                }).execute()
                print(f"   [OK] Created ASHA worker entry")
            
            fixed += 1
            
        except Exception as e:
            print(f"   [FAIL] Failed: {e}")
    else:
        print(f"[OK] User exists: {email}")

print("\n" + "=" * 60)
print(f"Done! Fixed {fixed} users.")
if fixed > 0:
    print("\n[!] IMPORTANT: Users were created with TEMPORARY passwords!")
    print("   They need to use the passwords shown above to log in,")
    print("   then change their password in their profile.")
print("=" * 60)
