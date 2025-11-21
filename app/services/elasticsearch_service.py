from elasticsearch import Elasticsearch
from typing import List, Dict, Any
import numpy as np
from ..config import settings

class ElasticsearchService:
    def __init__(self):
        self.es = Elasticsearch(settings.elasticsearch_host)
        self.index_name = "documents"
        self._initialized = False
    
    def _ensure_index_exists(self): 
        """Ensure the Elasticsearch index exists with the correct mapping."""
        if self._initialized:
            return
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "metadata": {"type": "object"},
                        "embedding": {"type": "dense_vector", "dims": settings.vector_size}
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)
        self._initialized = True
    
    def store_document_chunks(self, document_id: str, chunks: List[str], title: str = "Untitled"):
        """Store document chunks with OpenAI embeddings in Elasticsearch. Embeddings are generated inside, matching QdrantService interface."""
        self._ensure_index_exists()
        from .openai_service import get_embeddings
        from datetime import datetime
        embeddings = get_embeddings(chunks)
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Ensure embedding is a list (OpenAI returns lists, not numpy arrays)
            if not isinstance(embedding, list):
                embedding = list(embedding)
                
            doc = {
                "content": chunk,
                "metadata": {
                    "title": title,
                    "uploaded_at": datetime.now().isoformat(),
                    "document_id": document_id,
                    "chunk_index": i
                },
                "embedding": embedding  
            }
            self.es.index(index=self.index_name, body=doc)
    
    def search(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using OpenAI embeddings. Generates embeddings internally."""
        self._ensure_index_exists()
        from .openai_service import get_embeddings
        
        # Get embedding for query
        query_embedding = get_embeddings([text])[0]
        
        # Ensure it's a list
        if not isinstance(query_embedding, list):
            query_embedding = list(query_embedding)
        
        # Perform kNN search using script_score
        query = {
            "size": top_k,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            }
        }
        
        response = self.es.search(index=self.index_name, body=query)
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                'content': hit['_source']['content'],
                'metadata': hit['_source']['metadata'],
                'score': hit['_score']
            })
        
        return results
