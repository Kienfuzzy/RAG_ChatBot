# RAG System - FastAPI + Qdrant

A semantic search system built with FastAPI and Qdrant. Search through startup data using natural language queries.

## Features

- 🔍 Neural search with Sentence Transformers
- 🚀 FastAPI with automatic docs
- 📊 Qdrant vector database
- 🐳 Docker support

## Quick Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 3. Prepare data
cd scripts
python prepare_data.py
python upload_to_qdrant.py

# 4. Run API
uvicorn app.main:app --reload
```

**Visit:** http://localhost:8000/docs

## Usage

**Search startups:**
```bash
curl -X POST "http://localhost:8000/neural-search/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI startup", "limit": 5}'
```

## Project Structure

```
├── app/                   # FastAPI application
│   ├── main.py           # API entry point
│   ├── routers/          # API endpoints
│   └── services/         # Business logic
├── scripts/              # Data preparation
├── test_fastapi/         # FastAPI tutorials
├── test_qdrant/          # Qdrant tutorials
└── data/                 # Dataset storage
```

## Technologies

- FastAPI - Web framework
- Qdrant - Vector database
- Sentence Transformers - Text embeddings
- Docker - Containerization
