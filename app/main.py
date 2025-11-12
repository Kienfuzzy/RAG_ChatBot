from fastapi import FastAPI, Depends
from .dependencies import get_query_token, get_token_header
from .routers import items, users, vectors, neural_search

app = FastAPI(
    title="RAG Chatbot API",
    description="A FastAPI backend for RAG (Retrieval-Augmented Generation) system with Qdrant vector database",
    version="1.0.0",
    dependencies=[Depends(get_query_token)]
)


app.include_router(users.router)
app.include_router(items.router)
app.include_router(vectors.router)
app.include_router(neural_search.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
