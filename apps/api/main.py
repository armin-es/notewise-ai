from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
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
async def create_session():
    session_id = str(uuid.uuid4())
    logger.info(f"Creating new session: {session_id}")
    # Create a fresh engine for this user
    sessions[session_id] = get_chat_engine()
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
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    
    if session_id not in sessions:
        # Lazy init if session lost (server restart)
        logger.warning(f"Session {session_id} not found, creating new engine.")
        sessions[session_id] = get_chat_engine()
    
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
