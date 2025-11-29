from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notewise-api")

# 2. Initialize App
app = FastAPI(title="NoteWise AI API", version="0.1.0")

# 3. Configure CORS (Allow Next.js Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Data Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# 5. Routes
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "ok", "service": "notewise-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Phase 1: Echo Chat Endpoint.
    Receives a message and echoes it back.
    """
    logger.info(f"Received chat message: {request.message}")
    
    # Mock Response (Echo)
    mock_response = f"Echo: {request.message}"
    
    return ChatResponse(response=mock_response)

if __name__ == "__main__":
    import uvicorn
    # Run with: python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)

