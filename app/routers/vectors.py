from fastapi import APIRouter, HTTPException, Depends
from app.services.neural_searcher import NeuralSearcher
from app.models.vector_models import VectorSearchRequest, SearchResults, VectorSearchResponse
from app.dependencies import get_token_header
from typing import List
import uuid

router = APIRouter(
    prefix="/vectors",
    tags=["vectors"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# Initialize NeuralSearcher service
neural_searcher = NeuralSearcher()

@router.post("/search", response_model=SearchResults)
async def search_vectors(request: VectorSearchRequest):
    """Search for similar vectors in the specified collection."""
    try:
        results = neural_searcher.search(
            text=request.query,
            limit=request.limit
        )
        
        search_responses = [
            VectorSearchResponse(
                id=str(result["id"]),
                score=result.get("score", 0),
                payload=result["payload"]
            )
            for result in results
        ]
        
        return SearchResults(
            results=search_responses,
            total=len(search_responses),
            query=request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/collections/{collection_name}")
async def create_collection(collection_name: str, vector_size: int = 1536):
    """Create a new vector collection."""
    try:
        neural_searcher._ensure_collection_exists()
        return {"message": f"Collection '{collection_name}' ensured successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")

@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a vector collection."""
    try:
        neural_searcher.delete_collection(collection_name)
        return {"message": f"Collection '{collection_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")