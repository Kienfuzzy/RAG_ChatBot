
from openai import OpenAI
from ..config import settings
import logging
import time
from typing import List

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Service class for OpenAI API interactions, suitable for FastAPI dependency injection.
    """
    def __init__(self, api_key: str = None, timeout: float = 30.0, max_retries: int = 2):
        self.api_key = api_key or settings.openai_api_key
        logger.info(f"Initializing OpenAI client with API key: {self.api_key[:20]}...")
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=timeout,
            max_retries=max_retries
        )

    def get_embeddings(self, texts: List[str], model: str = "text-embedding-3-small", batch_size: int = 100) -> List[list]:
        """
        Generate embeddings for a list of text chunks using OpenAI API.
        Args:
            texts (list of str): The text chunks to embed.
            model (str): The embedding model to use.
            batch_size (int): Number of texts per API call.
        Returns:
            list: List of embedding vectors (list of floats).
        """
        if not isinstance(texts, list):
            texts = [texts]
        embeddings = []
        logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
        start_time = time.time()

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_start = time.time()
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=model
                )
                # Ensure embeddings are plain lists, not numpy arrays or other types
                batch_embeddings = [list(item.embedding) if hasattr(item.embedding, '__iter__') else item.embedding 
                                  for item in response.data]
                embeddings.extend(batch_embeddings)
                logger.info(f"Batch {i//batch_size + 1} ({len(batch)} texts) took {time.time() - batch_start:.2f}s")
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise

        total_time = time.time() - start_time
        logger.info(f"Total embedding generation took {total_time:.2f}s for {len(texts)} texts")
        return embeddings