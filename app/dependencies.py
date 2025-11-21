from typing import Annotated
from fastapi import Header, HTTPException
from .config import settings


async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != settings.secret_key:
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def get_query_token(token: str):
    if token != settings.query_token:
        raise HTTPException(status_code=400, detail="No query token provided")


# Service singletons - created once and reused
_qdrant_service = None
_elasticsearch_service = None


def get_qdrant_service():
    """Dependency to get QdrantService instance."""
    global _qdrant_service
    if _qdrant_service is None:
        from .services.qdrant_service import QdrantService
        _qdrant_service = QdrantService()
    return _qdrant_service


def get_elasticsearch_service():
    """Dependency to get ElasticsearchService instance."""
    global _elasticsearch_service
    if _elasticsearch_service is None:
        from .services.elasticsearch_service import ElasticsearchService
        _elasticsearch_service = ElasticsearchService()
    return _elasticsearch_service