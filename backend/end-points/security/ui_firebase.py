"""
Firebase Security Module
Handles Firebase user authentication and validation for Hoopie application.
Only allows users with @u-factor.io email domain in non-production environments.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
import firebase_admin
from firebase_admin import auth, credentials
import os
import logging
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        # Use default credentials in Cloud Run environment
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

# Create router instead of FastAPI app
router = APIRouter(
    prefix="/security",
    tags=["Firebase Security"],
    responses={404: {"description": "Not found"}},
)
# app = FastAPI()

# Get environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "hoopie-dev")

# Allowed email domains for Google OAuth authentication
ALLOWED_DOMAINS = ["u-factor.io", "deloitte.pt"]

# Google OAuth provider identifiers
GOOGLE_PROVIDERS = ["google.com", "firebase"]

class UserCreationEvent(BaseModel):
    """Firebase Auth user creation event data"""
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    provider_id: str = "firebase"
    provider_data: Optional[list] = None

class UserValidationRequest(BaseModel):
    """Request to validate a user"""
    uid: str
    email: EmailStr

def is_production_environment() -> bool:
    """Check if current environment is production"""
    return ENVIRONMENT.lower() == "prod" or "prod" in PROJECT_ID.lower()

def is_email_allowed(email: str) -> bool:
    """Check if email domain is allowed for Google OAuth"""
    if not email:
        return False
    
    return any(email.lower().endswith(f"@{domain.lower()}") for domain in ALLOWED_DOMAINS)

def is_google_auth_user(user_record) -> bool:
    """Check if user authenticated via Google OAuth"""
    try:
        # Check provider data for Google OAuth
        for provider in user_record.provider_data:
            if provider.provider_id == "google.com":
                return True
        return False
    except (AttributeError, TypeError):
        return False

def should_validate_user(user_record) -> tuple[bool, str]:
    """
    Determine if user should be validated based on authentication method.
    Returns (should_validate, reason)
    """
    try:
        # Only validate Google OAuth users
        if not is_google_auth_user(user_record):
            return False, "non_google_auth"
        
        # Google OAuth user - validate domain
        return True, "google_auth_user"
    except Exception:
        # If we can't determine auth method, skip validation to be safe
        return False, "unknown_auth_method"

async def delete_unauthorized_user(uid: str, email: str) -> bool:
    """Delete an unauthorized user account"""
    try:
        auth.delete_user(uid)
        logger.info(f"Successfully deleted unauthorized user: {email} (UID: {uid})")
        return True
    except Exception as error:
        logger.error(f"Error deleting user {email} (UID: {uid}): {error}")
        return False

@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Hoopie Firebase Security API",
        "status": "healthy",
        "environment": ENVIRONMENT,
        "project": PROJECT_ID,
        "security_enabled": not is_production_environment()
    }

@router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "project": PROJECT_ID,
        "firebase_initialized": len(firebase_admin._apps) > 0,
        "security_policy": "active" if not is_production_environment() else "disabled"
    }

@router.post("/webhook/user-created")
async def handle_user_creation(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint to handle Firebase user creation events.
    This should be called by a Firebase Extension or custom trigger.
    """
    try:
        # Parse the incoming webhook data
        data = await request.json()
        
        logger.info(f"Received user creation event: {data}")
        
        # Extract user information
        uid = data.get("uid")
        email = data.get("email")
        
        if not uid:
            raise HTTPException(status_code=400, detail="Missing user UID")
        
        # Skip validation in production
        if is_production_environment():
            logger.info(f"Production environment - allowing user {email} (UID: {uid})")
            return {"status": "allowed", "reason": "production_environment"}
        
        # Get full user record to check authentication method
        try:
            user_record = auth.get_user(uid)
        except auth.UserNotFoundError:
            logger.error(f"User {uid} not found in Firebase")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if this user should be validated (Google OAuth only)
        should_validate, validation_reason = should_validate_user(user_record)
        
        if not should_validate:
            logger.info(f"Skipping validation for user {email} (UID: {uid}) - Reason: {validation_reason}")
            return {
                "status": "allowed", 
                "reason": validation_reason,
                "email": email,
                "message": "Non-Google OAuth users are not subject to domain restrictions"
            }
        
        # Validate email domain for Google OAuth users
        if not is_email_allowed(email):
            logger.warning(f"Unauthorized Google OAuth email domain: {email} (UID: {uid})")
            
            # Delete user in background
            background_tasks.add_task(delete_unauthorized_user, uid, email)
            
            return {
                "status": "rejected",
                "reason": "unauthorized_google_domain",
                "email": email,
                "allowed_domains": [f"@{domain}" for domain in ALLOWED_DOMAINS],
                "message": "Google OAuth users must use approved email domains"
            }
        
        logger.info(f"Google OAuth user authorized: {email} (UID: {uid})")
        return {
            "status": "allowed",
            "reason": "authorized_google_domain",
            "email": email,
            "allowed_domains": [f"@{domain}" for domain in ALLOWED_DOMAINS]
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as error:
        logger.error(f"Error processing user creation: {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/validate-user")
async def validate_user(validation_request: UserValidationRequest):
    """
    Endpoint to validate a user manually.
    Can be called by frontend or other services.
    """
    try:
        uid = validation_request.uid
        email = validation_request.email
        
        # Skip validation in production
        if is_production_environment():
            return {"status": "allowed", "reason": "production_environment"}
        
        # Check if user exists in Firebase
        try:
            user_record = auth.get_user(uid)
            if user_record.email != email:
                raise HTTPException(status_code=400, detail="Email mismatch")
        except auth.UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if this user should be validated (Google OAuth only)
        should_validate, validation_reason = should_validate_user(user_record)
        
        if not should_validate:
            logger.info(f"Skipping validation for user {email} (UID: {uid}) - Reason: {validation_reason}")
            return {
                "status": "allowed", 
                "reason": validation_reason,
                "email": email,
                "message": "Non-Google OAuth users are not subject to domain restrictions"
            }
        
        # Validate email domain for Google OAuth users
        if not is_email_allowed(email):
            logger.warning(f"Validation failed for unauthorized Google OAuth email: {email} (UID: {uid})")
            return {
                "status": "rejected",
                "reason": "unauthorized_google_domain",
                "email": email,
                "allowed_domains": [f"@{domain}" for domain in ALLOWED_DOMAINS],
                "message": "Google OAuth users must use approved email domains"
            }
        
        return {
            "status": "allowed",
            "reason": "authorized_google_domain",
            "email": email,
            "allowed_domains": [f"@{domain}" for domain in ALLOWED_DOMAINS]
        }
        
    except Exception as error:
        logger.error(f"Error validating user: {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/user/{uid}")
async def delete_user(uid: str):
    """
    Endpoint to delete a user account.
    Only available in non-production environments.
    """
    if is_production_environment():
        raise HTTPException(status_code=403, detail="User deletion not allowed in production")
    
    try:
        user = auth.get_user(uid)
        auth.delete_user(uid)
        
        logger.info(f"User deleted: {user.email} (UID: {uid})")
        return {
            "status": "deleted",
            "uid": uid,
            "email": user.email
        }
        
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as error:
        logger.error(f"Error deleting user {uid}: {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/validate-all")
async def validate_all_users():
    """
    Endpoint to validate all existing users.
    Only available in non-production environments.
    """
    if is_production_environment():
        raise HTTPException(status_code=403, detail="Bulk validation not allowed in production")
    
    try:
        # List all users
        page = auth.list_users()
        google_oauth_authorized = []
        google_oauth_unauthorized = []
        non_google_oauth_users = []
        
        while page:
            for user in page.users:
                # Check if this user should be validated (Google OAuth only)
                should_validate, validation_reason = should_validate_user(user)
                
                if not should_validate:
                    non_google_oauth_users.append({
                        "uid": user.uid,
                        "email": user.email,
                        "status": "not_validated",
                        "reason": validation_reason,
                        "message": "Non-Google OAuth users are not subject to domain restrictions"
                    })
                else:
                    # Google OAuth user - check domain
                    if is_email_allowed(user.email):
                        google_oauth_authorized.append({
                            "uid": user.uid,
                            "email": user.email,
                            "status": "authorized"
                        })
                    else:
                        google_oauth_unauthorized.append({
                            "uid": user.uid,
                            "email": user.email,
                            "status": "unauthorized"
                        })
            
            # Get next page
            page = page.get_next_page()
        
        total_users = len(google_oauth_authorized) + len(google_oauth_unauthorized) + len(non_google_oauth_users)
        
        return {
            "total_users": total_users,
            "google_oauth_authorized": len(google_oauth_authorized),
            "google_oauth_unauthorized": len(google_oauth_unauthorized),
            "non_google_oauth_users": len(non_google_oauth_users),
            "google_oauth_authorized_users": google_oauth_authorized,
            "google_oauth_unauthorized_users": google_oauth_unauthorized,
            "non_google_oauth_users_list": non_google_oauth_users,
            "allowed_domains": [f"@{domain}" for domain in ALLOWED_DOMAINS],
            "message": "Only Google OAuth users are subject to domain validation"
        }
        
    except Exception as error:
        logger.error(f"Error validating users: {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Export the router for use in main application
__all__ = ["router"]