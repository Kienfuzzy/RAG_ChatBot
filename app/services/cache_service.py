import redis
import json
from typing import Optional, Dict, Any


class CacheService:
    """Simple Redis cache service for search results."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                # after 2 seconds raise an error if cannot connect
                socket_connect_timeout=2
            )
            # Test connection
            self.redis.ping()
            self.enabled = True
        except Exception as e:
            self.enabled = False
    
    def get(self, key: str) -> Optional[Dict[Any, Any]]:
        """
        Get value from Redis cache.
        Returns None if key doesn't exist or cache is disabled.
        """
        if not self.enabled:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            pass
        
        return None
    
    def set(self, key: str, value: Dict[Any, Any], ttl: int = 600):
        """
        Save value to Redis cache with TTL (Time To Live).
        
        Args:
            key: Cache key
            value: Data to cache (must be JSON serializable)
            ttl: Expiration time in seconds (default 10 minutes)
        """
        if not self.enabled:
            return
        
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            pass


# Global cache instance
cache = CacheService()
