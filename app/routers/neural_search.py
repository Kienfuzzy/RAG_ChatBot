from fastapi import APIRouter, Depends
from app.services.neural_searcher import NeuralSearcher  # Import the tutorial class
from app.dependencies import get_token_header

router = APIRouter(
    prefix="/neural-search",
    tags=["neural-search"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# Create neural searcher instance (from tutorial, using config)
neural_searcher = NeuralSearcher()  # Uses default collection from config

@router.get("/search")
def search_startup(q: str):
    """Search startups using neural search (tutorial implementation)."""
    return {"result": neural_searcher.search(text=q)}

@router.get("/search-enhanced")
def search_startup_enhanced(q: str, limit: int = 5):
    """Enhanced version with configurable limit."""
    # You can extend the tutorial class here
    results = neural_searcher.search(text=q)
    return {
        "query": q,
        "limit": limit,
        "results": results[:limit],
        "total_found": len(results)
    }