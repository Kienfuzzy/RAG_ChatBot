from pydantic import BaseModel
from typing import List, Optional

class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query: str
    limit: int = 5
    collection_name: str = "startups"

class VectorSearchResponse(BaseModel):
    """Response model for vector search."""
    id: str
    score: float
    payload: dict

class SearchResults(BaseModel):
    """Search results container."""
    results: List[VectorSearchResponse]
    total: int
    query: str

class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    text: str
    metadata: Optional[dict] = None
    collection_name: str = "startups"

class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    id: str
    message: str