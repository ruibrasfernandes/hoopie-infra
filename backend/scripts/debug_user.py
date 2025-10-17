#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import sys
import json
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
            return True
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            return False
    return True

def get_user_details(email):
    """Get full Firebase Auth user details by email."""
    try:
        user = auth.get_user_by_email(email)

        # Build comprehensive user details dictionary
        user_details = {
            "uid": user.uid,
            "email": user.email,
            "email_verified": user.email_verified,
            "display_name": user.display_name,
            "phone_number": user.phone_number,
            "photo_url": user.photo_url,
            "disabled": user.disabled,
            "metadata": {
                "creation_timestamp": user.user_metadata.creation_timestamp,
                "last_sign_in_timestamp": user.user_metadata.last_sign_in_timestamp,
                "last_refresh_timestamp": user.user_metadata.last_refresh_timestamp
            },
            "custom_claims": user.custom_claims,
            "provider_data": [
                {
                    "uid": provider.uid,
                    "email": provider.email,
                    "phone_number": provider.phone_number,
                    "display_name": provider.display_name,
                    "photo_url": provider.photo_url,
                    "provider_id": provider.provider_id
                }
                for provider in user.provider_data
            ],
            "tokens_valid_after_timestamp": user.tokens_valid_after_timestamp,
            "tenant_id": user.tenant_id
        }

        return user_details

    except auth.UserNotFoundError:
        print(f"❌ User with email '{email}' not found.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Error retrieving user: {e}", file=sys.stderr)
        return None

def get_firestore_user_data(uid):
    """Get Firestore user document data by UID."""
    try:
        db = firestore.client()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict()
        else:
            return None
    except Exception as e:
        print(f"⚠️  Error retrieving Firestore user document: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_user.py <user_email>")
        print("Example: python debug_user.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]

    if not initialize_firebase():
        sys.exit(1)

    user_details = get_user_details(email)

    if user_details:
        print("=== Firebase Auth User Details ===")
        print(json.dumps(user_details, indent=2, default=str))

        # Fetch Firestore user document
        uid = user_details.get("uid")
        if uid:
            print("\n=== Firestore User Document ===")
            firestore_data = get_firestore_user_data(uid)
            if firestore_data:
                print(json.dumps(firestore_data, indent=2, default=str))
            else:
                print("⚠️  No data in Firestore user document")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()