from openai import OpenAI
from ..config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

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
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            response = client.embeddings.create(
                input=batch,
                model=model
            )
            embeddings.extend([item.embedding for item in response.data])
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise
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