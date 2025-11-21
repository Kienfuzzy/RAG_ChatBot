# RAG System - FastAPI + Qdrant

A semantic search system built with FastAPI and Qdrant. Search through startup data using natural language queries.

## Features

- 🔍 Neural search with Sentence Transformers
- 🚀 FastAPI with automatic docs
- 📊 Qdrant vector database
- 🐳 Docker support

## Quick Setup


```bash
# 1. Install dependencies with Poetry
# (If you have a requirements.txt and want to import those dependencies, run:)
poetry add $(cat requirements.txt)
# Or, if you want to install from pyproject.toml (recommended for ongoing work):
poetry install

# 2. Start Qdrant, Elasticsearch, and Redis (Docker/Homebrew, not Poetry)
# IMPORTANT: All services must be running before starting the FastAPI server!

# First time setup:
docker run -d --name qdrant -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Install and start Redis (for caching):
brew install redis
redis-server

# To restart the containers in the future, use:
docker start qdrant elasticsearch

# To stop the containers, use:
docker stop qdrant elasticsearch

# To check if containers are running:
docker ps

# 3. Prepare data (run scripts in Poetry environment)
poetry run python scripts/prepare_data.py
poetry run python scripts/upload_to_qdrant.py

# 4. Run API (FastAPI backend)
# Development mode (auto-reloads on code changes):
poetry run uvicorn app.main:app --reload

# Production mode (faster, no auto-reload):
# poetry run uvicorn app.main:app

# 5. Start chatbot UI
poetry run streamlit run chatbot_ui.py
```


**Visit:** http://localhost:8000/docs

---

**Note:**
- Poetry manages all Python dependencies and virtual environments for you.
- You do NOT need to activate or use a `venv` manually if you use Poetry.
- Qdrant and Elasticsearch run in Docker and must be started before running the API.
- Redis runs separately via Homebrew for caching search results.
- The FastAPI server uses lazy initialization - services only connect when first used.

**Troubleshooting:**
- If `/docs` won't load: Make sure Docker containers are running (`docker ps`)
- If you see connection timeouts: Restart Docker containers (`docker restart qdrant elasticsearch`)
- Elasticsearch requires security disabled for local development (`xpack.security.enabled=false`)

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
