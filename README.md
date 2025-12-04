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

# 2. Start ALL services with Docker Compose
# IMPORTANT: All services must be running before starting the FastAPI server!

# Start all services (Qdrant, Elasticsearch, Redis, MySQL):
docker-compose up -d

# To restart all services:
docker-compose restart

# To stop all services:
docker-compose stop

# To check if services are running:
docker-compose ps

# 3. Prepare data (run scripts in Poetry environment)
poetry run python scripts/prepare_data.py
poetry run python scripts/upload_to_qdrant.py

# 4. Initialize MySQL database (for tabular search)
poetry run python scripts/init_database.py

# 5. Run API (FastAPI backend)
# Development mode (auto-reloads on code changes):
poetry run uvicorn app.main:app --reload

# Production mode (faster, no auto-reload):
# poetry run uvicorn app.main:app

# 6. Start chatbot UI
poetry run streamlit run chatbot_ui.py
```



**Visit:** http://localhost:8000/docs

---

**Note:**
- Poetry manages all Python dependencies and virtual environments for you.
- You do NOT need to activate or use a `venv` manually if you use Poetry.
- All services (Qdrant, Elasticsearch, Redis, MySQL) run in Docker via docker-compose.
- The FastAPI server uses lazy initialization - services only connect when first used.

**Troubleshooting:**
- If `/docs` won't load: Make sure services are running (`docker-compose ps`)
- If you see connection timeouts: Restart services (`docker-compose restart`)
- Check logs: `docker-compose logs <service_name>` (e.g., `docker-compose logs mysql`)
- If migrating from old docker run commands, remove old containers first:
  ```bash
  docker stop qdrant elasticsearch redis 2>/dev/null
  docker rm qdrant elasticsearch redis 2>/dev/null
  docker-compose up -d
  ```


## MySQL Database Setup

### 🚀 Quick Start

1. **Start MySQL with Docker Compose**
  ```bash
  docker-compose up -d mysql
  ```
  Chờ ~10 giây để MySQL khởi động.

2. **Install Python dependencies**
  ```bash
  pip install mysql-connector-python
  ```

3. **Initialize database**
  ```bash
  python scripts/init_database.py
  ```

### 🔍 Verify Database

**Connect to MySQL:**
```bash
docker exec -it products_db mysql -uraguser -pragpass123 products
```

**Query examples:**
```sql
-- Show all products
SELECT * FROM products;

-- Headphones under $100
SELECT name, price, rating FROM products 
WHERE category = 'headphones' AND price < 100;

-- Top rated products
SELECT name, category, price, rating FROM products 
WHERE rating >= 4.5 
ORDER BY rating DESC;

-- Products by brand
SELECT * FROM products WHERE brand = 'Sony';
```

### 📊 Database Schema

```sql
products (
   id INT PRIMARY KEY,
   name VARCHAR(255),
   category VARCHAR(100),  -- 'headphones', 'laptops', 'accessories'
   price DECIMAL(10,2),
   brand VARCHAR(100),
   specs JSON,
   rating DECIMAL(2,1),
   review_count INT,
   created_at TIMESTAMP
)
```

### 🧪 Test Queries

```python
from app.services.database_service import DatabaseService

db = DatabaseService()

# Price filter
results = db.query(category='headphones', max_price=100)

# Rating filter
results = db.query(min_rating=4.5)

# Combined filters
results = db.query(
   category='laptops',
   max_price=1500,
   min_rating=4.5,
   limit=10
)
```

### 🔧 Configuration

Edit `.env` or `app/config.py`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=products
MYSQL_USER=raguser
MYSQL_PASSWORD=ragpass123
```

---

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
