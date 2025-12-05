from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.algorithms import RSAAlgorithm
import httpx
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import List, Optional, Dict
from rag.engine import get_chat_engine
from llama_index.core.base.response.schema import Response
from llama_index.core.chat_engine.types import BaseChatEngine
import uuid

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notewise-api")

# 2. Initialize App
app = FastAPI(title="NoteWise AI API", version="0.1.0")

# Security Scheme (Clerk)
security = HTTPBearer()

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    jwks_url = os.getenv("CLERK_JWKS_URL")  # We need to set this!

    if not jwks_url:
        # Fallback if URL not in env (try to deduce or use default)
        # For now, fail if not set
        logger.error("CLERK_JWKS_URL not set")
        raise HTTPException(status_code=500, detail="Server misconfiguration: Missing JWKS URL")

    try:
        # Fetch JWKS (Cache this in production!)
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            jwks = response.json()

        # Decode Header to find Key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key in JWKS
        key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        
        if not key_data:
             raise HTTPException(status_code=401, detail="Invalid token key ID")

        # Construct Public Key
        public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))

        # Verify Token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False} # Audience varies, usually verify_signature is enough for this
        )
        
        return payload["sub"] # Returns User ID

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# 3. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Session Management
# Store chat engines per session_id
# In production, use Redis or Postgres for this!
sessions: Dict[str, BaseChatEngine] = {}

@app.post("/session")
async def create_session(user_id: str = Depends(verify_clerk_token)):
    # We can now scope sessions to user_id if we want
    # For now, we still generate a random session_id for the chat instance, 
    # but we could map user_id -> session_id in a database.
    
    session_id = str(uuid.uuid4())
    logger.info(f"Creating new session for User {user_id}: {session_id}")
    # Create a fresh engine for this user
    sessions[session_id] = get_chat_engine(user_id=user_id)
    return {"session_id": session_id}

# 5. Data Models
class Source(BaseModel):
    filename: str
    score: float
    text: str

class ChatRequest(BaseModel):
    message: str
    session_id: str  # Required now

class ChatResponse(BaseModel):
    response: str
    sources: List[Source] = []

# 6. Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notewise-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(verify_clerk_token)):
    session_id = request.session_id
    
    if session_id not in sessions:
        # Lazy init if session lost (server restart)
        logger.warning(f"Session {session_id} not found, creating new engine.")
        sessions[session_id] = get_chat_engine(user_id=user_id)
    
    chat_engine = sessions[session_id]

    logger.info(f"[{session_id}] Received message: {request.message}")
    
    # Call LlamaIndex
    response: Response = chat_engine.chat(request.message)
    
    # Extract Sources
    sources = []
    if hasattr(response, 'source_nodes'):
        for node in response.source_nodes:
            score = node.score if node.score else 0.0
            file_path = node.metadata.get('file_path', 'Unknown')
            filename = file_path.split('/')[-1]
            
            sources.append(Source(
                filename=filename,
                score=score,
                text=node.node.get_content()[:200] + "..."
            ))
            
    return ChatResponse(
        response=str(response),
        sources=sources
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
