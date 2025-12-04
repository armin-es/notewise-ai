# NoteWise AI

> A full-stack RAG (Retrieval-Augmented Generation) application that acts as a Personal Knowledge Assistant. Built with Next.js 14, FastAPI, LlamaIndex, and PostgreSQL (pgvector).

## Features

- **Real-time Chat:** Talk to your personal notes using natural language.
- **RAG Pipeline:** Ingests Markdown files, chunks them, and embeds them using OpenAI.
- **Semantic Search:** Finds relevant context using Vector Embeddings.
- **Citations:** Shows exactly which file and text snippet answered your question.
- **Memory:** Remembers your conversation context (Session-based).

## Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS.
- **Backend:** FastAPI (Python), LlamaIndex (RAG Framework).
- **Database:** PostgreSQL with `pgvector` extension.
- **AI:** OpenAI GPT-4o & `text-embedding-3-small`.

## Getting Started

### Prerequisites

- Docker (for the Database)
- Node.js (v18+) & pnpm
- Python (v3.10+) & pip
- OpenAI API Key

### 1. Setup Database

```bash
cd notewise-ai
docker-compose up -d
```

### 2. Setup Backend (API)

```bash
cd notewise-ai/apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_key_here" > .env
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/notewise_db" >> .env

# Run Ingestion (Load your notes)
# Ensure you update the target path in rag/ingestion.py first!
python rag/ingestion.py

# Start Server
python -m uvicorn main:app --reload --port 8000
```

### 3. Setup Frontend (Web)

```bash
cd notewise-ai/apps/web
pnpm install
pnpm dev
```

Visit **[http://localhost:3000](http://localhost:3000)** to chat!
