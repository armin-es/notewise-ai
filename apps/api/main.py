from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List, Optional
from rag.engine import get_chat_engine
from llama_index.core.base.response.schema import Response

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

# 4. Initialize Chat Engine
chat_engine = None

@app.on_event("startup")
async def startup_event():
    global chat_engine
    try:
        logger.info("Initializing Chat Engine...")
        chat_engine = get_chat_engine()
        logger.info("Chat Engine ready.")
    except Exception as e:
        logger.error(f"Failed to initialize Chat Engine: {e}")

# 5. Data Models
class Source(BaseModel):
    filename: str
    score: float
    text: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: List[Source] = []

# 6. Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notewise-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Chat engine not ready")

    logger.info(f"Received chat message: {request.message}")
    
    # Call LlamaIndex
    response: Response = chat_engine.chat(request.message)
    
    # Extract Sources
    sources = []
    if hasattr(response, 'source_nodes'):
        for node in response.source_nodes:
            # Calculate a readable score (0-100%)
            score = node.score if node.score else 0.0
            
            # Get filename from metadata (LlamaIndex stores it there automatically)
            file_path = node.metadata.get('file_path', 'Unknown')
            filename = file_path.split('/')[-1] # Just get the name "notes.md"
            
            sources.append(Source(
                filename=filename,
                score=score,
                text=node.node.get_content()[:200] + "..." # Preview of text
            ))
            
    return ChatResponse(
        response=str(response),
        sources=sources
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
