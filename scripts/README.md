# Data Processing Scripts

This folder contains scripts for preparing and uploading data to Qdrant vector database.

## Setup

1. Make sure Qdrant is running:
   ```bash
   docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
   ```

2. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

## Scripts

### 1. prepare_data.py
Prepares the startup dataset for vector search:
- Loads SentenceTransformer model (all-MiniLM-L6-v2)
- Reads startup data from `data/startups_demo.json`
- Encodes descriptions into 384-dimensional vectors
- Saves vectors as `startup_vectors.npy`

**Usage:**
```bash
python scripts/prepare_data.py
```

### 2. upload_to_qdrant.py
Uploads processed data to Qdrant:
- Creates "startups" collection
- Uploads vectors and metadata to Qdrant
- Uses batch processing for efficiency

**Usage:**
```bash
python scripts/upload_to_qdrant.py
```

## Execution Order

1. First run data preparation:
   ```bash
   python scripts/prepare_data.py
   ```

2. Then upload to Qdrant:
   ```bash
   python scripts/upload_to_qdrant.py
   ```

3. Your FastAPI app will now be able to search the data via `/neural-search/search`