from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from ..config import settings
from .openai_service import get_embeddings
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class NeuralSearcher:
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or settings.default_collection
        self.qdrant_client = QdrantClient(settings.qdrant_url)
        # Ensure collection exists on initialization
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists with the correct vector size (1536)."""
        try:
            # Create the collection if it doesn't exist
            if not self.qdrant_client.collection_exists(self.collection_name):
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def store_document_chunks(self, document_id: str, chunks: list, title: str = "Untitled"):
        """Store document chunks with OpenAI embeddings in Qdrant."""
        try:
            embeddings = get_embeddings(chunks)
            points = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                points.append({
                    "id": str(uuid.uuid4()),  # Generate a valid UUID for each chunk
                    "vector": embedding,
                    "payload": {
                        "document_id": document_id,
                        "title": title,
                        "chunk_index": i,
                        "content": chunk,
                        "uploaded_at": datetime.now().isoformat()
                    }
                })
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error storing document chunks: {e}")
            raise

    def search(self, text: str, limit: int = 5):
        """Search for similar documents using OpenAI embeddings."""
        try:
            # Use OpenAI embeddings for consistency with document upload
            vector = get_embeddings([text])[0]

            # Search for closest vectors in the collection
            search_result = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=None,
                limit=limit,
            ).points
            
            # Return payloads with similarity scores
            return [hit.payload for hit in search_result]
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    def file_exists(self, filename: str):
        """Check if a file exists in Qdrant by searching for its title."""
        try:
            # Search for all documents
            search_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            # Check if any document has this filename as title
            points, next_page_offset = search_result
            for point in points:
                if point.payload.get("title") == filename:
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False

    def get_all_files(self):
        """Get list of all unique files stored in Qdrant with metadata."""
        try:
            # Get all documents from Qdrant
            search_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            points, next_page_offset = search_result
            files_info = {}
            
            # Group chunks by filename and collect metadata
            for point in points:
                payload = point.payload
                filename = payload.get("title", "Unknown")
                
                if filename not in files_info:
                    files_info[filename] = {
                        "filename": filename,
                        "document_id": payload.get("document_id"),
                        "uploaded_at": payload.get("uploaded_at"),
                        "total_chunks": 0
                    }
                
                files_info[filename]["total_chunks"] += 1
            
            return list(files_info.values())
            
        except Exception as e:
            logger.error(f"Error getting all files: {e}")
            raise