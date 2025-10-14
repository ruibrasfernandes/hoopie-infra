import os
import uuid
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

load_dotenv()



# Import security module
# from security.ui_firebase import ENVIRONMENT, router as security_router

VERTEX_AI_READY = False
AGENT_READY = False
AGENT_ID = None

project_id = ""
location = ""
app_name = ""
# Connect to Agent Engine - One-time discovery at startup
# app_name = "Hoopie SDM Agent"
remote_app = None


# In-memory session storage (userId -> sessionId)
# In production, this should be replaced with a database
sessions = {}

# Initialize Vertex AI
def initialize_vertexAI():
    """
    Funtion to Initialize Vertex AI
    """
    global VERTEX_AI_READY, project_id, location, app_name

    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "hoopie-dev")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-southwest1")
        environment = os.environ.get("ENVIRONMENT", "dev")
        app_name = f"hoopie-agent-{environment}"

        vertexai.init(project=project_id, location=location)
        VERTEX_AI_READY = True
        print(f"✅ Vertex AI initialized successfully for project {project_id} in {location}")
    except Exception as e:
        VERTEX_AI_READY = False
        print(f"❌ Error initializing Vertex AI: {e}")



def discover_latest_agent():
    """Discover the latest agent once at startup"""
    global remote_app, AGENT_READY, AGENT_ID

    if not VERTEX_AI_READY:
        return

    try:
        print(f"🔍 Discovering latest agent: {app_name}")
        # Get the most recent agent with this display name (ONE TIME LOOKUP)
        ae_apps = list(agent_engines.list(filter=f'display_name="{app_name}"'))

        if ae_apps:
            # Sort by creation time to get the most recent
            ae_apps.sort(key=lambda x: x.create_time, reverse=True)
            remote_app = ae_apps[0]

            AGENT_READY = True
            AGENT_ID = remote_app.name.split('/')[-1]  # Extract ID from resource name
            print(f"✅ Agent discovered and cached")
            print(f"   Agent ID: {AGENT_ID}")
            print(f"   Created: {remote_app.create_time}")
        else:
            print(f"❌ No agents found with display name: {app_name}")

    except Exception as e:
        AGENT_READY = False
        print(f"❌ Error discovering agent: {e}")

# Initialize Vertex AI and discover agent once at startup
initialize_vertexAI()
discover_latest_agent()

# FastAPI app
app = FastAPI(
    title="Agent Proxy API",
    description="Proxy service for Vertex AI Agent Engine with Firebase Security",
    version="1.0.0"
)

# Include the security router
# app.include_router(security_router)

# CORS middleware - More explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React dev port
        "https://hoopie-dev.web.app",  # Firebase dev
        "https://hoopie-stag.web.app",  # Firebase staging  
        "https://hoopie-prod.web.app",  # Firebase production
        "https://hoopie-web-dev.web.app",  # Firebase dev (legacy)
        "https://hoopie-web-stag.web.app",  # Firebase staging (legacy)
        "https://hoopie-web-prod.web.app",  # Firebase production (legacy)
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"]
)

class QueryRequest(BaseModel):
    message: str
    userId: str  # Will be email for better readability
    firebaseUid: str = None  # Firebase UID for session management
    sessionId: str = None

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Agent proxy running",
        "vertex_ai_ready": VERTEX_AI_READY,
        "agent_ready": AGENT_READY
    }

def get_or_create_session(user_id: str, provided_session_id: str = None):
    """Get existing session or create new one for a user"""
    if provided_session_id and provided_session_id in sessions.values():
        # Existing session provided and valid
        return provided_session_id, False
    
    if user_id in sessions:
        # User has existing session
        return sessions[user_id], False
    
    # Create new session
    new_session_id = f"session_{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    sessions[user_id] = new_session_id
    return new_session_id, True

@app.post("/query")
async def query_agent(request: QueryRequest):
    # Use Firebase UID for session management (fallback to userId if firebaseUid not provided)
    print("I'm here")
    session_key = request.firebaseUid or request.userId
    # Always manage sessions properly, regardless of agent readiness
    session_id, session_created = get_or_create_session(session_key, request.sessionId)
    
    # Check if agent is ready
    if not AGENT_READY or remote_app is None:
        # Return mock response if agent not ready, but with proper session management
        return {
            "success": True,
            "text": f"[MOCK] Agent not ready. Mock response to: '{request.message}' from user {request.userId}",
            "session_id": session_id,
            "user_id": request.userId,
            "session_created": session_created
        }
    
    try:
        # For real agent, we need to handle Vertex AI sessions differently
        # but still maintain our local session tracking
        vertex_session_id = None
        
        if session_created or not request.sessionId:
            # Create new Vertex AI session only when we created a new local session
            try:
                session_response = remote_app.create_session(user_id=request.userId)
                print(f"Session creation response: {session_response}")
                
                # Handle different response formats
                if hasattr(session_response, 'id'):
                    vertex_session_id = session_response.id
                elif isinstance(session_response, dict) and 'id' in session_response:
                    vertex_session_id = session_response['id']
                elif hasattr(session_response, 'output') and hasattr(session_response.output, 'id'):
                    vertex_session_id = session_response.output.id
                elif isinstance(session_response, dict) and 'output' in session_response and 'id' in session_response['output']:
                    vertex_session_id = session_response['output']['id']
                else:
                    vertex_session_id = str(session_response)
                
                print(f"✅ Created new Vertex AI session {vertex_session_id} for user {request.userId}")
                # Store mapping of our session to Vertex session (for future use)
                # For now, we'll just use the vertex session directly
                sessions[session_key] = vertex_session_id
                session_id = vertex_session_id
            except Exception as e:
                print(f"❌ Session creation error: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
        else:
            # Use existing session (could be our local session or vertex session)
            vertex_session_id = session_id
        
        # Send message to agent
        try:
            print(f'Sending message to {AGENT_ID}, user: {request.userId}, session: {vertex_session_id}')
            response_text = ""
            for event in remote_app.stream_query(
                user_id=request.userId,
                session_id=vertex_session_id,
                message=request.message
            ):
                print(f"Agent event: {event}")
                # Extract text from different event formats
                if hasattr(event, 'text'):
                    response_text += event.text
                elif hasattr(event, 'content') and hasattr(event.content, 'parts'):
                    # Handle content.parts[].text format
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
                elif isinstance(event, dict):
                    # Handle dictionary format - this is the main format we get
                    if 'text' in event:
                        response_text += event['text']
                    elif 'content' in event and 'parts' in event['content']:
                        # Handle {'content': {'parts': [{'text': '...'}]}} - This is the actual format!
                        for part in event['content']['parts']:
                            if 'text' in part:
                                response_text += part['text']
                                print(f"✅ Extracted text: {part['text']}")
                    elif 'content' in event:
                        # Sometimes content might be direct text
                        response_text += str(event['content'])
                        print(f"✅ Extracted content: {event['content']}")
                    else:
                        print(f"❓ Unknown event format: {event}")
                else:
                    response_text += str(event)
            
            if not response_text:
                response_text = "Agent processed your message but returned no text response."
            
            return {
                "success": True,
                "text": response_text,
                "session_id": session_id,
                "user_id": request.userId,
                "session_created": session_created
            }
            
        except Exception as e:
            print(f"❌ Agent query error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to query agent: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ General error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/clear-session")
async def clear_session(request: dict):
    """Clear session for a specific user"""
    user_id = request.get("userId") or request.get("firebaseUid")
    if not user_id:
        raise HTTPException(status_code=400, detail="userId or firebaseUid is required")
    
    if user_id in sessions:
        old_session = sessions[user_id]
        del sessions[user_id]
        return {
            "success": True,
            "message": f"Session cleared for user {user_id}",
            "cleared_session": old_session
        }
    else:
        return {
            "success": True,
            "message": f"No session found for user {user_id}",
            "cleared_session": None
        }

@app.get("/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "success": True,
        "sessions": sessions,
        "session_count": len(sessions)
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)