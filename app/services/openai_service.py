from openai import OpenAI
from ..config import settings
import logging
import time

logger = logging.getLogger(__name__)

# Initialize client with timeout to prevent hanging
logger.info(f"Initializing OpenAI client with API key: {settings.openai_api_key[:20]}...")
client = OpenAI(
    api_key=settings.openai_api_key,
    timeout=30.0,
    max_retries=2
)

def get_embeddings(texts, model="text-embedding-3-small", batch_size=100):
    """
    Generate embeddings for a list of text chunks using OpenAI API.
    Args:
        texts (list of str): The text chunks to embed.
        model (str): The embedding model to use.
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
            response = client.embeddings.create(
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

# Example usage (for testing only):
if __name__ == "__main__":
    test_chunks = [
        "This is the first chunk.",
        "Here is another chunk of text.",
        "Final chunk for embedding."
    ]
    embeddings = get_embeddings(test_chunks)
    print(f"Returned {len(embeddings)} embeddings. First embedding (first 5 values): {embeddings[0][:5]}")