# RAG Chatbot - FastAPI Project

## Local Development Setup (No Docker)

### 1. Create and activate a virtual environment
On macOS/Linux:
```sh
python3 -m venv venv
source venv/bin/activate
```
On Windows:
```sh
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies
```sh
pip install -r requirements.txt
```

### 3. Run the FastAPI app
Option 1: Using Uvicorn
```sh
uvicorn app.main:app --reload
```
Option 2: Using FastAPI's built-in dev server (FastAPI >= 0.110.0)
```sh
fastapi dev app/main.py
```

- Access the docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Docker Setup (Recommended)

### 1. Build the Docker image
```sh
docker build -t rag-chatbot .
```

### 2. Run the Docker container
```sh
docker run -p 8000:8000 rag-chatbot
```

- Access the docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

**Choose either local or Docker setup. No need to do both!**
