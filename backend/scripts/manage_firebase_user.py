#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, auth
import os
import re
import getpass

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    """
    # Check if the app is already initialized
    if not firebase_admin._apps:
        # Try to get the project ID from the environment variable
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
            return False

        try:
            # Use Application Default Credentials
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                "projectId": project_id,
            })
            print(f"Firebase app initialized for project: {project_id}")
            return True
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            return False
    return True

def get_custom_claims():
    """Gets custom claims from user input."""
    role = ""
    while role not in ["superuser", "admin", "operator"]:
        role = input("Enter role (superuser, admin, operator): ")
    customers_str = input("Enter customers (comma-separated, leave empty for all): ")
    nickname = input("Enter nickname (optional): ")

    if not customers_str:
        customers = ["all"]
    else:
        customers = [c.strip() for c in customers_str.split(",")]

    custom_claims = {
        "role": role,
        "customers": customers,
    }
    if nickname:
        custom_claims["nickname"] = nickname
    return custom_claims

def validate_and_format_phone(phone):
    """
    Validates and formats phone number to E.164 format.
    Returns None if phone is empty or invalid.
    """
    if not phone or not phone.strip():
        return None
    
    # Remove all spaces, dashes, and parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Ensure it starts with +
    if not phone.startswith('+'):
        print(f"Warning: Phone number should start with '+' and country code. Skipping phone number.")
        return None
    
    # Basic validation - should be between 10 and 15 digits after the +
    # (Most countries need at least 10 total digits including country code)
    digits_only = phone[1:]  # Remove the +
    if not digits_only.isdigit() or len(digits_only) < 10 or len(digits_only) > 15:
        print(f"Warning: Invalid phone number format. Should be +[country code][number] with 10-15 digits total (including country code). Skipping phone number.")
        print(f"Example for Portugal: +351999887766 (12 digits total)")
        return None
    
    return phone

def main():
    """
    Main function to manage Firebase users.
    """
    if not initialize_firebase():
        return

    auth_method = ""
    while auth_method not in ["email", "google"]:
        auth_method = input("Choose authentication method (email, google): ")

    if auth_method == "email":
        email = ""
        while not email:
            email = input("Enter email: ")
        name = input("Enter name (optional): ")
        phone_input = input("Enter phone (optional, format: +countrycode number, e.g., +351999887766): ")
        phone = validate_and_format_phone(phone_input)
        
        custom_claims = get_custom_claims()

        try:
            user = auth.get_user_by_email(email)
            print(f"User with email {email} already exists.")
            enforce = input("Do you want to enforce the custom claims? (yes/no): ")
            if enforce.lower() == "yes":
                auth.set_custom_user_claims(user.uid, custom_claims)
                print("Custom claims updated successfully.")
                # Update other user properties if needed
                update_params = {}
                if name:
                    update_params["display_name"] = name
                if phone:
                    update_params["phone_number"] = phone
                if update_params:
                    auth.update_user(user.uid, **update_params)
                    print("User properties updated.")
        except auth.UserNotFoundError:
            user_attrs = {
                "email": email,
                "email_verified": True,
            }
            if name:
                user_attrs["display_name"] = name
            if phone:
                user_attrs["phone_number"] = phone
            
            # Get password for the new user
            password = getpass.getpass("Enter a password for the new user: ")
            user_attrs["password"] = password
            
            print(f"Creating user with attributes: {dict((k, v if k != 'password' else '***') for k, v in user_attrs.items())}")
            
            try:
                new_user = auth.create_user(**user_attrs)
                print(f"✅ User created with UID: {new_user.uid}")
                
                # Set custom claims
                auth.set_custom_user_claims(new_user.uid, custom_claims)
                print(f"✅ Custom claims set: {custom_claims}")
                
                print(f"🎉 User with email {email} created successfully!")
                
            except Exception as create_error:
                print(f"❌ Error creating user: {create_error}")
                print(f"   User attributes attempted: {user_attrs}")
                return
                
        except auth.ConfigurationNotFoundError:
            print("❌ Error: Invalid email address or Email/Password sign-in is not enabled in your Firebase project.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    elif auth_method == "google":
        email = ""
        while not email:
            email = input("Enter Google email: ")
        
        custom_claims = get_custom_claims()

        try:
            user = auth.get_user_by_email(email)
            print(f"User with email {email} already exists.")
            enforce = input("Do you want to enforce the custom claims? (yes/no): ")
            if enforce.lower() == "yes":
                auth.set_custom_user_claims(user.uid, custom_claims)
                print("Custom claims updated successfully.")
        except auth.UserNotFoundError:
            print(f"User with email {email} not found. Please ensure the user has already signed in with Google in your application.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()