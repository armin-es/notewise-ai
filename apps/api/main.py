from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from rag.engine import get_chat_engine

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notewise-api")

# 2. Initialize App
app = FastAPI(title="NoteWise AI API", version="0.1.0")

# 3. Configure CORS (Allow Next.js Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Initialize Chat Engine (Global Singleton)
# We do this lazily or on startup to avoid recreating it every request
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
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# 6. Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notewise-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Phase 3: RAG Chat Endpoint.
    """
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Chat engine not ready")

    logger.info(f"Received chat message: {request.message}")
    
    # Call LlamaIndex RAG
    # This retrieves documents -> calls GPT-4 -> returns answer
    response = chat_engine.chat(request.message)
    
    return ChatResponse(response=str(response))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
