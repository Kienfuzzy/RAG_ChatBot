import re

def semantic_chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks at natural boundaries (sentences, paragraphs)
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Target size of each chunk
        overlap (int): Characters to overlap between chunks
    
    Returns:
        list: List of text chunks split at natural boundaries
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    # Split text into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed chunk_size, start a new chunk
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from previous chunk
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # Add the final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def semantic_chunk_documents(documents, chunk_size=500, overlap=50):
    """
    Chunk documents using semantic boundaries (sentences/paragraphs)
    
    Args:
        documents (list): List of document dictionaries
        chunk_size (int): Target size of each chunk
        overlap (int): Characters to overlap between chunks
    
    Returns:
        list: List of semantically chunked documents
    """
    chunked_documents = []
    
    for doc_index, doc in enumerate(documents):
        # Get the text content to chunk
        text_content = doc.get('description', '')
        
        # Skip if no content
        if not text_content:
            continue
        
        # Chunk the text semantically
        chunks = semantic_chunk_text(text_content, chunk_size, overlap)
        
        # Create document for each chunk
        for chunk_index, chunk in enumerate(chunks):
            # Calculate simple metrics
            word_count = len(chunk.split())
            sentence_count = len(re.split(r'[.!?]+', chunk))
            
            chunked_doc = {
                'id': f"semantic_doc_{doc_index}_chunk_{chunk_index}",
                'content': chunk,
                'original_name': doc.get('name', 'Unknown'),
                'original_city': doc.get('city', 'Unknown'),
                'chunk_type': 'semantic',
                'chunk_index': chunk_index,
                'total_chunks': len(chunks),
                'word_count': word_count,
                'sentence_count': max(1, sentence_count - 1)  # Subtract 1 for empty split at end
            }
            chunked_documents.append(chunked_doc)
    
    return chunked_documents

def split_by_paragraphs(text, max_chunk_size=1000):
    """
    Split text by paragraphs, keeping related content together
    
    Args:
        text (str): Text to split
        max_chunk_size (int): Maximum size before forcing a split
    
    Returns:
        list: List of paragraph-based chunks
    """
    # Split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If adding this paragraph would exceed max size, start new chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Example usage
if __name__ == "__main__":
    # Test with sample text
    sample_text = """This is the first sentence of our document. It contains important information about startups.
    
    This is a second paragraph with more details. It explains how the business model works and what makes it unique.
    
    The final paragraph concludes our document. It summarizes the key points and provides contact information."""
    
    print("Original text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Test semantic chunking
    semantic_chunks = semantic_chunk_text(sample_text, chunk_size=100, overlap=20)
    print(f"Semantic chunks ({len(semantic_chunks)}):")
    for i, chunk in enumerate(semantic_chunks):
        print(f"\nChunk {i+1}: {chunk}")
    
    print("\n" + "="*50 + "\n")
    
    # Test paragraph splitting
    paragraph_chunks = split_by_paragraphs(sample_text, max_chunk_size=150)
    print(f"Paragraph chunks ({len(paragraph_chunks)}):")
    for i, chunk in enumerate(paragraph_chunks):
        print(f"\nParagraph {i+1}: {chunk}")