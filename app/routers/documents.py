from asyncio.log import logger
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Union, List
import uuid
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Import pipeline components
from app.document_loader.loader import load_text_file
from app.document_loader.chunker import chunk_text, chunk_document
from app.services.neural_searcher import NeuralSearcher
from app.dependencies import get_token_header

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class DocumentResponse(BaseModel):
    document_id: str
    message: str
    chunks_created: int

neural_searcher = NeuralSearcher()  # Handles search + Qdrant storage

@router.get("/")
def list_files():
    """List all files stored in Qdrant"""
    try:
        files = neural_searcher.get_all_files()
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/check/{filename}")
def check_file(filename: str):
    """Check if a file exists in Qdrant"""
    exists = neural_searcher.file_exists(filename)
    return {"filename": filename, "exists": exists}

@router.post("/upload-file")
async def upload_text_file(file: UploadFile = File(...)):
    """Upload text files (.txt, .md) following the indexing pipeline: read → clean/chunk → embed → store"""
    try:
        # Validate file type - only text files now
        allowed_extensions = ['.txt', '.md']
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"Only {', '.join(allowed_extensions)} files supported")
        
        doc_id = str(uuid.uuid4())
        temp_file_path = f"temp_{doc_id}{os.path.splitext(file.filename)[1]}"
        
        # Step 1: Save and load document
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        # Load as Document object with metadata
        document = load_text_file(temp_file_path)
        if not document:
            raise HTTPException(status_code=400, detail="Failed to load file")
        
        # Step 2: Clean and chunk the document
        chunked_docs = chunk_document(document, chunk_size=500, overlap=50)
        chunks = [chunk_doc['content'] for chunk_doc in chunked_docs]
        logger.info(f"Created {len(chunks)} chunks from {file.filename}")
        
        # Step 3: Generate embeddings and store in Qdrant
        chunks_stored = neural_searcher.store_document_chunks(
            document_id=doc_id,
            chunks=chunks,
            title=file.filename
        )
        
        # Cleanup
        os.remove(temp_file_path)
        
        return DocumentResponse(
            document_id=doc_id,
            message=f"Text file processed successfully: {file.filename}",
            chunks_created=chunks_stored
        )
        
    except Exception as e:
        try:
            if 'temp_file_path' in locals():
                os.remove(temp_file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/search")
async def search_documents(search: SearchRequest):
    """Search uploaded documents"""
    try:
        results = neural_searcher.search(text=search.query, limit=search.limit)
        
        return {
            "query": search.query,
            "limit": search.limit,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
