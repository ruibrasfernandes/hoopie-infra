#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, auth
import os
import time

from dotenv import load_dotenv

load_dotenv(override=True)

GOOGLE_CLOUD_PROJECT=os.environ.get("GOOGLE_CLOUD_PROJECT")
print(f"GOOGLE_CLOUD_PROJECT={GOOGLE_CLOUD_PROJECT}")



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

def test_user_creation():
    """Test user creation with immediate verification."""
    if not initialize_firebase():
        return
    
    # Test user data
    test_email = "test.user.delete.me@example.com"
    user_attrs = {
        "email": test_email,
        "email_verified": True,
        "display_name": "Test User DELETE ME"
    }
    
    print(f"🧪 Testing user creation...")
    print(f"   Email: {test_email}")
    print(f"   Attributes: {user_attrs}")
    
    try:
        # Step 1: Create user
        print(f"\n1️⃣ Creating user...")
        new_user = auth.create_user(**user_attrs)
        print(f"   ✅ User created with UID: {new_user.uid}")
        print(f"   📧 Email: {new_user.email}")
        print(f"   👤 Display Name: {new_user.display_name}")
        
        # Step 2: Immediately try to fetch by UID
        print(f"\n2️⃣ Immediately checking by UID...")
        try:
            fetched_user = auth.get_user(new_user.uid)
            print(f"   ✅ User found by UID!")
            print(f"   📧 Email: {fetched_user.email}")
            print(f"   👤 Display Name: {fetched_user.display_name}")
        except Exception as e:
            print(f"   ❌ User NOT found by UID: {e}")
        
        # Step 3: Try to fetch by email
        print(f"\n3️⃣ Checking by email...")
        try:
            fetched_user = auth.get_user_by_email(test_email)
            print(f"   ✅ User found by email!")
            print(f"   🆔 UID: {fetched_user.uid}")
            print(f"   👤 Display Name: {fetched_user.display_name}")
        except Exception as e:
            print(f"   ❌ User NOT found by email: {e}")
        
        # Step 4: Wait a bit and try again
        print(f"\n4️⃣ Waiting 2 seconds and checking again...")
        time.sleep(2)
        try:
            fetched_user = auth.get_user(new_user.uid)
            print(f"   ✅ User found by UID after wait!")
        except Exception as e:
            print(f"   ❌ User STILL NOT found by UID after wait: {e}")
        
        # Step 5: Clean up - delete the test user
        print(f"\n5️⃣ Cleaning up - deleting test user...")
        try:
            auth.delete_user(new_user.uid)
            print(f"   ✅ Test user deleted successfully")
        except Exception as e:
            print(f"   ⚠️ Could not delete test user: {e}")
        
    except Exception as create_error:
        print(f"   ❌ Error creating user: {create_error}")
        print(f"   Type: {type(create_error)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_creation()