from typing import Optional, Dict, Any
import numpy as np
from app.services.cache_service import cache
from app.services.openai_service import get_embeddings


class SemanticCacheService:
    """
    Lightweight semantic cache using OpenAI embeddings and Redis.
    Caches search results and uses cosine similarity to find similar queries.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
                                 0.90 = very similar, 0.85 = somewhat similar
        """
        self.similarity_threshold = similarity_threshold
        self.cache = cache
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get(self, query: str) -> Optional[Dict[Any, Any]]:
        """
        Get cached result for semantically similar query.
        
        Returns:
            Cached results if similar query found, None otherwise
        """
        if not self.cache.enabled:
            return None
        
        try:
            # Generate embedding for the query
            query_embedding = get_embeddings([query])[0]
            
            # Get the index of all cached queries
            cache_index = self.cache.get("semantic_cache:index")
            
            if not cache_index:
                return None
            
            # Find most similar query
            best_match = None
            best_similarity = 0.0
            
            for cached_query, cached_embedding in cache_index.items():
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_query
            
            # Check if similarity is above threshold
            if best_match and best_similarity >= self.similarity_threshold:
                # Get the actual cached result
                cached_result = self.cache.get(f"semantic_cache:result:{best_match}")
                
                if cached_result:
                    # Add similarity score to cached result
                    cached_result['cache_similarity'] = round(best_similarity, 3)
                    return cached_result
            
        except Exception as e:
            print(f"[SEMANTIC CACHE ERROR] {e}")
        
        return None
    
    def set(self, query: str, result: Dict[Any, Any], ttl: int = 600):
        """
        Cache result with query embedding.
        
        Args:
            query: The search query
            result: The search result to cache
            ttl: Time to live in seconds
        """
        if not self.cache.enabled:
            return
        
        try:
            # Generate embedding
            query_embedding = get_embeddings([query])[0]
            
            # Update the cache index
            cache_index = self.cache.get("semantic_cache:index") or {}
            cache_index[query] = query_embedding
            self.cache.set("semantic_cache:index", cache_index, ttl=ttl)
            
            # Cache the actual result
            self.cache.set(f"semantic_cache:result:{query}", result, ttl=ttl)
            
        except Exception as e:
            print(f"[SEMANTIC CACHE ERROR] {e}")


# Global semantic cache instance with 0.90 similarity threshold
semantic_cache = SemanticCacheService(similarity_threshold=0.90)