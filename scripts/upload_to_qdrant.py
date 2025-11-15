import json
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

print("Connecting to Qdrant...")
# Create a client object for Qdrant
client = QdrantClient("http://localhost:6333")

collection_name = "startups"

print(f"Checking if collection '{collection_name}' exists...")
# Check if the collection exists
if client.collection_exists(collection_name):
    print(f"Deleting collection '{collection_name}'...")
    client.delete_collection(collection_name)
    print(f"Collection '{collection_name}' deleted successfully.")
print(f"Creating collection '{collection_name}'...")
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
print(f"Collection '{collection_name}' created")

print("Loading data and vectors...")
# Load the startup data
fd = open("./data/startups_demo.json")
# payload is now an iterator over startup data
payload = list(map(json.loads, fd))

# Load all vectors into memory
vectors = np.load("./startup_vectors.npy")

# Check if vectors already exist in the collection
existing_vector_count = client.count(collection_name).count
if existing_vector_count > 0:
    print(f"Collection '{collection_name}' already contains {existing_vector_count} vectors. Skipping upload.")
else:
    print(f"Uploading {len(vectors)} vectors to Qdrant...")
    # Upload the data
    client.upload_collection(
        collection_name=collection_name,
        vectors=vectors,
        payload=payload,
        ids=None,  # Vector ids will be assigned automatically
        batch_size=256,  # How many vectors will be uploaded in a single request?
    )
    print("Vectors uploaded to Qdrant successfully!")

fd.close()
print("You can now use the 'startups' collection for neural search.")