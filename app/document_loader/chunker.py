def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks with overlap
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
    
    Returns:
        list: List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
        if end >= len(text):
            break
        
    return chunks

def chunk_documents(documents, chunk_size=500, overlap=50):
    """
    Chunk a list of documents (like startup data)
    
    Args:
        documents (list): List of document dictionaries
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
    
    Returns:
        list: List of chunked documents with metadata
    """
    chunked_documents = []
    
    for doc_index, doc in enumerate(documents):
        text_content = doc.get('description', '')
        
        if not text_content:
            continue
    
        chunks = chunk_text(text_content, chunk_size, overlap)
        for chunk_index, chunk in enumerate(chunks):
            chunked_doc = {
                'id': f"doc_{doc_index}_chunk_{chunk_index}",
                'content': chunk,
                'original_name': doc.get('name', 'Unknown'),
                'original_city': doc.get('city', 'Unknown'),
                'chunk_index': chunk_index,
                'total_chunks': len(chunks)
            }
            chunked_documents.append(chunked_doc)
    
    return chunked_documents

# Example usage
if __name__ == "__main__":
    sample_text = "This is a long piece of text that we want to chunk into smaller pieces. Each piece should have some overlap with the previous piece to maintain context. This helps in processing large documents."
    
    chunks = chunk_text(sample_text, chunk_size=50, overlap=10)
    
    print("Original text:")
    print(sample_text)
    print(f"\nSplit into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk}")