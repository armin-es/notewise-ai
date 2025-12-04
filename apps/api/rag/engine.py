import os
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from sqlalchemy import make_url

# Load env vars
load_dotenv(Path(__file__).parent.parent / ".env")

# Configure Settings (Must match ingestion!)
Settings.llm = OpenAI(model="gpt-4o")
Settings.embedding = OpenAIEmbedding(model="text-embedding-3-small")

def get_chat_engine():
    """
    Connects to the existing Vector Store and returns a Chat Engine.
    """
    
    # 1. Connect to Postgres (Dynamic from Env)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set in .env")

    url = make_url(database_url)

    vector_store = PGVectorStore.from_params(
        database=url.database,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name="data_embeddings",
        embed_dim=1536,
    )

    # 2. Load Index from Vector Store (No ingestion happens here)
    # We tell LlamaIndex: "The data is already in this vector store"
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # 3. Create Chat Engine
    # "context" mode: Retrieves relevant chunks and adds them to context
    return index.as_chat_engine(chat_mode="context", system_prompt=(
        "You are NoteWise AI, a personal knowledge assistant."
        "You have access to the user's personal notes and interview stories."
        "Always answer based on the provided context."
        "If the answer is not in the notes, say you don't know."
        "Keep answers concise and helpful."
    ))
