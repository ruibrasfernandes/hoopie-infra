#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, auth
import os

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
            return False
        
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id})
            print(f"Firebase app initialized for project: {project_id}")
            return True
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            return False
    return True

def check_user_by_email(email):
    """Check if a user exists by email and show their details."""
    try:
        user = auth.get_user_by_email(email)
        print(f"✅ User found by email!")
        print(f"   UID: {user.uid}")
        print(f"   Email: {user.email}")
        print(f"   Email Verified: {user.email_verified}")
        print(f"   Display Name: {user.display_name}")
        print(f"   Phone: {user.phone_number}")
        print(f"   Created: {user.user_metadata.creation_timestamp}")
        print(f"   Last Sign In: {user.user_metadata.last_sign_in_timestamp}")
        print(f"   Custom Claims: {user.custom_claims}")
        return True
    except auth.UserNotFoundError:
        print(f"❌ User with email {email} not found.")
        return False
    except Exception as e:
        print(f"❌ Error checking user by email: {e}")
        return False

def check_user_by_uid(uid):
    """Check if a user exists by UID and show their details."""
    try:
        user = auth.get_user(uid)
        print(f"✅ User found by UID!")
        print(f"   UID: {user.uid}")
        print(f"   Email: {user.email}")
        print(f"   Email Verified: {user.email_verified}")
        print(f"   Display Name: {user.display_name}")
        print(f"   Phone: {user.phone_number}")
        print(f"   Created: {user.user_metadata.creation_timestamp}")
        print(f"   Last Sign In: {user.user_metadata.last_sign_in_timestamp}")
        print(f"   Custom Claims: {user.custom_claims}")
        return True
    except auth.UserNotFoundError:
        print(f"❌ User with UID {uid} not found.")
        return False
    except Exception as e:
        print(f"❌ Error checking user by UID: {e}")
        return False

def main():
    if not initialize_firebase():
        return
    
    # Check the specific user by email
    email = "petavares@deloitte.pt"
    uid = "2ILqwdmgwnRTmahldjId5FJjOaN2"  # UID from the creation attempt
    
    print(f"🔍 Checking user by email: {email}")
    found_by_email = check_user_by_email(email)
    
    print(f"\n🔍 Checking user by UID: {uid}")
    found_by_uid = check_user_by_uid(uid)
    
    if not found_by_email and not found_by_uid:
        # List all users to see what exists
        print("\n📋 Listing all users in the project:")
        try:
            page = auth.list_users()
            user_count = 0
            for user in page.users:
                user_count += 1
                print(f"  {user_count}. Email: {user.email} | UID: {user.uid} | Display Name: {user.display_name}")
            
            if user_count == 0:
                print("  No users found in this project.")
            else:
                print(f"  Total users: {user_count}")
                
        except Exception as e:
            print(f"Error listing users: {e}")
    
    # Double-check project info
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    print(f"\n🏢 Currently connected to project: {project_id}")
    print("   Make sure this matches the Firebase Console project you're checking!")

if __name__ == "__main__":
    main()