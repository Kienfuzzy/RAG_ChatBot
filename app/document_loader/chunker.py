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

def chunk_document(document, chunk_size=500, overlap=50):
    """
    Chunk a single Document object (works with any document type)
    
    Args:
        document: Document object with page_content and metadata
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
    
    Returns:
        list: List of chunked documents with preserved metadata
    """
    # Handle both Document objects, dicts, and plain text
    if hasattr(document, 'page_content'):
        # Object with attributes (langchain Document)
        text_content = document.page_content
        base_metadata = document.metadata.copy()
    elif isinstance(document, dict) and 'page_content' in document:
        # Dict format (simple loader)
        text_content = document['page_content']
        base_metadata = document.get('metadata', {}).copy()
    else:
        # Fallback for plain text
        text_content = str(document)
        base_metadata = {}
    
    if not text_content.strip():
        return []
    
    chunks = chunk_text(text_content, chunk_size, overlap)
    chunked_documents = []
    
    for chunk_index, chunk in enumerate(chunks):
        chunk_metadata = {
            **base_metadata,  # Preserve original metadata
            'chunk_index': chunk_index,
            'total_chunks': len(chunks),
            'chunk_size': len(chunk)
        }
        
        # Create a simple dict for backward compatibility
        chunked_doc = {
            'content': chunk,
            'metadata': chunk_metadata
        }
        chunked_documents.append(chunked_doc)
    
    return chunked_documents

def chunk_documents(documents, chunk_size=500, overlap=50):
    """
    Chunk a list of documents (works with any document type)
    
    Args:
        documents (list): List of Document objects or text strings
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
    
    Returns:
        list: List of all chunked documents
    """
    all_chunked_docs = []
    
    for document in documents:
        chunked_docs = chunk_document(document, chunk_size, overlap)
        all_chunked_docs.extend(chunked_docs)
    
    return all_chunked_docs

# Example usage
if __name__ == "__main__":
    sample_text = "This is a long piece of text that we want to chunk into smaller pieces. Each piece should have some overlap with the previous piece to maintain context. This helps in processing large documents."
    
    chunks = chunk_text(sample_text, chunk_size=50, overlap=10)
    
    print("Original text:")
    print(sample_text)
    print(f"\nSplit into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk}")