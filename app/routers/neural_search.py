from fastapi import APIRouter, Depends
from app.dependencies import get_token_header, get_qdrant_service

router = APIRouter(
    prefix="/neural-search",
    tags=["neural-search"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get("/search")
def search_startup(q: str, qdrant_service = Depends(get_qdrant_service)):
    """Search startups using neural search (tutorial implementation)."""
    return {"result": qdrant_service.search(text=q)}

@router.get("/search-enhanced")
def search_startup_enhanced(q: str, limit: int = 5, qdrant_service = Depends(get_qdrant_service)):
    """Enhanced version with configurable limit."""
    # You can extend the tutorial class here
    results = qdrant_service.search(text=q)
    return {
        "query": q,
        "limit": limit,
        "results": results[:limit],
        "total_found": len(results)
    }