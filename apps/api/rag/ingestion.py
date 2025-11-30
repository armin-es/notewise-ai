import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import psycopg2

# Configure LlamaIndex Settings
Settings.llm = OpenAI(model="gpt-4o")
Settings.embedding = OpenAIEmbedding(model="text-embedding-3-small")

def ingest_notes():
    print("🚀 Starting ingestion...")

    # 1. Connect to Postgres
    db_name = "notewise_db"
    host = "localhost"
    password = "password"
    port = "5432"
    user = "postgres"

    # Create connection string/args
    url = "postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    vector_store = PGVectorStore.from_params(
        database=db_name,
        host=host,
        password=password,
        port=port,
        user=user,
        table_name="data_embeddings",
        embed_dim=1536,  # Dimensions for text-embedding-3-small
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 2. Load Documents
    # Target: The root 'notes' directory. 
    # We are in apps/api/rag/ingestion.py -> Go up 6 levels to reach root?
    # Let's use an absolute path logic based on where we run this script.
    
    # Assuming we run this from 'apps/api'
    # Root is ../../../../../
    
    # Let's try to find the "behavioral" folder as a test target first
    # to avoid ingesting the huge node_modules in projects/
    
    current_file = Path(__file__).resolve()
    # notewise-ai/apps/api/rag/ingestion.py
    
    # We want to reach /Users/armin/Documents - Local/notes/behavioral
    target_dir = Path("/Users/armin/Documents - Local/notes/behavioral")

    print(f"📂 Reading files from: {target_dir}")

    if not target_dir.exists():
        print(f"❌ Directory not found: {target_dir}")
        return

    # Load only markdown files
    documents = SimpleDirectoryReader(
        input_dir=str(target_dir),
        recursive=True,
        required_exts=[".md"]
    ).load_data()

    print(f"📄 Loaded {len(documents)} documents")

    # 3. Create Index (Chunks & Embeds & Saves to DB)
    print("🧠 Creating Vector Index (this calls OpenAI)...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    print("✅ Ingestion Complete! Vectors stored in Postgres.")

if __name__ == "__main__":
    ingest_notes()

