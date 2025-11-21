import os
from datetime import datetime

def load_text_file(file_path):
    """
    Load a text file - SIMPLIFIED VERSION (no langchain to avoid slow imports)
    
    Args:
        file_path (str): Path to the text file (.txt, .md)
    
    Returns:
        dict: Document dict with content and metadata
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Return simple dict structure that chunk_document can handle
        document = {
            'page_content': content,
            'metadata': {
                'source': file_path,
                'file_size': os.path.getsize(file_path),
                'loaded_at': datetime.now().isoformat(),
                'filename': os.path.basename(file_path),
                'file_type': os.path.splitext(file_path)[1]
            }
        }
        
        return document
        
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def load_documents_from_directory(directory_path):
    """
    Load all text files from a directory
    
    Args:
        directory_path (str): Path to the directory containing text files
    
    Returns:
        list: List of Document objects from all text files
    """
    documents = []
    supported_extensions = ['.txt', '.md']
    
    for filename in os.listdir(directory_path):
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension in supported_extensions:
            file_path = os.path.join(directory_path, filename)
            document = load_text_file(file_path)
            if document:
                documents.append(document)
                print(f"Loaded document from {filename} ({document.metadata['file_size']} bytes)")
    
    return documents

# Example usage
if __name__ == "__main__":
    # Test with your test documents directory
    test_dir = "../../test_documents"
    
    if os.path.exists(test_dir):
        documents = load_documents_from_directory(test_dir)
        print(f"Total documents loaded: {len(documents)}")
        
        # Show example of first document
        if documents:
            print("\nExample document:")
            print(f"Filename: {documents[0].metadata.get('filename', 'N/A')}")
            print(f"File size: {documents[0].metadata.get('file_size', 'N/A')} bytes")
            print(f"Content preview: {documents[0].page_content[:100]}...")
    else:
        print(f"Test directory not found: {test_dir}")
