import os
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from sqlalchemy import make_url

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Configure LlamaIndex Settings
Settings.llm = OpenAI(model="gpt-4o")
Settings.embedding = OpenAIEmbedding(model="text-embedding-3-small")

def ingest_notes():
    print("🚀 Starting ingestion...")

    # 1. Connect to Postgres (Dynamic from Env)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set in .env")

    # Parse URL to get params
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

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 2. Load Documents
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
