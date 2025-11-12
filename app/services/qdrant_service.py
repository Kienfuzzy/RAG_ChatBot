from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class QdrantService:
    """Service class for Qdrant vector database operations."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        
    def create_collection(self, collection_name: str, vector_size: int = 384):
        """Create a new collection in Qdrant."""
        try:
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Collection '{collection_name}' created successfully")
            else:
                logger.info(f"Collection '{collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def encode_text(self, text: str) -> List[float]:
        """Encode text to vector using SentenceTransformer."""
        return self.encoder.encode(text).tolist()
    
    def search_similar(self, collection_name: str, query: str, limit: int = 5):
        """Search for similar vectors in collection."""
        try:
            query_vector = self.encode_text(query)
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
            ).points
            return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in search_result]
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise