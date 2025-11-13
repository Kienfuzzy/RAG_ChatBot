import os
import json

def load_json_file(file_path):
    """
    Simple function to load a JSON Lines file (each line is a JSON object)
    
    Args:
        file_path (str): Path to the JSON file
    
    Returns:
        list: List of documents loaded from the file
    """
    documents = []
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Skip empty lines
                document = json.loads(line)
                documents.append(document)
    
    return documents

def load_documents_from_directory(directory_path):
    """
    Load all JSON files from a directory
    
    Args:
        directory_path (str): Path to the directory containing JSON files
    
    Returns:
        list: List of all documents from all JSON files
    """
    all_documents = []
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            documents = load_json_file(file_path)
            all_documents.extend(documents)
            print(f"Loaded {len(documents)} documents from {filename}")
    
    return all_documents

# Example usage
if __name__ == "__main__":
    # Define the path to the data directory
    DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
    
    # Load all documents from the data directory
    documents = load_documents_from_directory(DATA_DIR)
    
    print(f"Total documents loaded: {len(documents)}")
    
    # Show example of first document
    if documents:
        print("\nExample document:")
        print(f"Name: {documents[0].get('name', 'N/A')}")
        print(f"Description: {documents[0].get('description', 'N/A')[:100]}...")
        print(f"City: {documents[0].get('city', 'N/A')}")
