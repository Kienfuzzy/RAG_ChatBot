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
from app.dependencies import get_token_header, get_qdrant_service, get_elasticsearch_service
from app.services.query_processor import process_query
from app.services.semantic_cache_service import semantic_cache  # Import semantic cache

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

class HybridSearchRequest(BaseModel):
    query: str
    limit: int = 5
    qdrant_weight: float = 0.5  # Weight for Qdrant results (0-1)
    elasticsearch_weight: float = 0.5  # Weight for Elasticsearch results (0-1)

@router.get("/")
def list_files(qdrant_service = Depends(get_qdrant_service)):
    """List all files stored in Qdrant"""
    try:
        files = qdrant_service.get_all_files()
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/check/{filename}")
def check_file(filename: str, qdrant_service = Depends(get_qdrant_service)):
    """Check if a file exists in Qdrant"""
    exists = qdrant_service.file_exists(filename)
    return {"filename": filename, "exists": exists}

@router.post("/upload-file")
async def upload_text_file(
    file: UploadFile = File(...),
    qdrant_service = Depends(get_qdrant_service),
    elasticsearch_service = Depends(get_elasticsearch_service)
):
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
        import time
        chunk_start = time.time()
        chunked_docs = chunk_document(document, chunk_size=500, overlap=50)
        chunks = [chunk_doc['content'] for chunk_doc in chunked_docs]
        logger.info(f"Created {len(chunks)} chunks from {file.filename} in {time.time() - chunk_start:.2f}s")
        
        # Step 3: Store in both Qdrant and Elasticsearch (both generate embeddings internally)
        # Store in Qdrant
        qdrant_start = time.time()
        chunks_stored = qdrant_service.store_document_chunks(
            document_id=doc_id,
            chunks=chunks,
            title=file.filename
        )
        logger.info(f"Stored in Qdrant in {time.time() - qdrant_start:.2f}s")
        
        # Store in Elasticsearch
        es_start = time.time()
        elasticsearch_service.store_document_chunks(
            document_id=doc_id,
            chunks=chunks,
            title=file.filename
        )
        logger.info(f"Stored in Elasticsearch in {time.time() - es_start:.2f}s")
        
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

@router.post("/search-qdrant")
async def search_documents(search: SearchRequest, qdrant_service = Depends(get_qdrant_service)):
    """Search uploaded documents using Qdrant only"""
    try:
        # Process query before searching
        cleaned_query, intent = process_query(search.query)
        
        # Search with cleaned query
        results = qdrant_service.search(text=cleaned_query, limit=search.limit)
        
        return {
            "query": search.query,
            "cleaned_query": cleaned_query,
            "intent": intent,
            "limit": search.limit,
            "source": "qdrant",
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/search-elasticsearch")
async def search_elasticsearch(search: SearchRequest, elasticsearch_service = Depends(get_elasticsearch_service)):
    """Search uploaded documents using Elasticsearch only"""
    try:
        # Process query before searching
        cleaned_query, intent = process_query(search.query)
        
        # Search Elasticsearch (generates embeddings internally)
        results = elasticsearch_service.search(text=cleaned_query, top_k=search.limit)
        
        return {
            "query": search.query,
            "cleaned_query": cleaned_query,
            "intent": intent,
            "limit": search.limit,
            "source": "elasticsearch",
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/search-hybrid")
async def search_hybrid(
    search: HybridSearchRequest,
    qdrant_service = Depends(get_qdrant_service),
    elasticsearch_service = Depends(get_elasticsearch_service)
):
    """Hybrid search combining results from both Qdrant and Elasticsearch using weighted scoring"""
    try:
        # Step 1: Check semantic cache first (uses embeddings to find similar queries)
        normalized_query = search.query.strip()
        
        cached_results = semantic_cache.get(normalized_query)
        
        if cached_results:
            cached_results['cached'] = True
            return cached_results
        
        # Step 2: Cache miss - process query and do actual search
        cleaned_query, intent = process_query(normalized_query)
        
        # Search both systems (both generate embeddings internally)
        qdrant_results = qdrant_service.search(text=cleaned_query, limit=search.limit * 2)
        es_results = elasticsearch_service.search(text=cleaned_query, top_k=search.limit * 2)
        
        # Handle None results
        if qdrant_results is None:
            qdrant_results = []
        if es_results is None:
            es_results = []
        
        # Combine and rank results using weighted scoring
        combined_results = {}
        
        # Add Qdrant results with weight
        for i, result in enumerate(qdrant_results):
            doc_id = result.get('document_id', '')
            chunk_idx = result.get('chunk_index', 0)
            key = f"{doc_id}_{chunk_idx}"
            
            # Normalize score (higher rank = higher score)
            normalized_score = (len(qdrant_results) - i) / len(qdrant_results)
            
            combined_results[key] = {
                'content': result.get('content', ''),
                'document_id': doc_id,
                'chunk_index': chunk_idx,
                'title': result.get('title', ''),
                'qdrant_score': normalized_score,
                'es_score': 0.0,
                'combined_score': normalized_score * search.qdrant_weight
            }
        
        # Add Elasticsearch results with weight
        for i, result in enumerate(es_results):
            doc_id = result['metadata'].get('document_id', '')
            chunk_idx = result['metadata'].get('chunk_index', 0)
            key = f"{doc_id}_{chunk_idx}"
            
            # Normalize score
            normalized_score = (len(es_results) - i) / len(es_results)
            
            if key in combined_results:
                # Update existing entry
                combined_results[key]['es_score'] = normalized_score
                combined_results[key]['combined_score'] += normalized_score * search.elasticsearch_weight
            else:
                # Add new entry
                combined_results[key] = {
                    'content': result.get('content', ''),
                    'document_id': doc_id,
                    'chunk_index': chunk_idx,
                    'title': result['metadata'].get('title', ''),
                    'qdrant_score': 0.0,
                    'es_score': normalized_score,
                    'combined_score': normalized_score * search.elasticsearch_weight
                }
        
        # Sort by combined score and return top K
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:search.limit]
        
        # Step 3: Build response
        response = {
            "query": search.query,
            "cleaned_query": cleaned_query,
            "intent": intent,
            "limit": search.limit,
            "source": "hybrid",
            "weights": {
                "qdrant": search.qdrant_weight,
                "elasticsearch": search.elasticsearch_weight
            },
            "results": sorted_results,
            "total_found": len(sorted_results),
            "cached": False
        }
        
        # Step 4: Save to semantic cache (10 minutes TTL)
        semantic_cache.set(normalized_query, response, ttl=600)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")
