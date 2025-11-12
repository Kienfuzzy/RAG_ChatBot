import json
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

print("Connecting to Qdrant...")
# Create a client object for Qdrant
client = QdrantClient("http://localhost:6333")

print("Creating collection 'startups'...")
# Create a new collection for startup vectors (following tutorial exactly)
if not client.collection_exists("startups"):
    client.create_collection(
        collection_name="startups",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("Collection 'startups' created")
else:
    print("Collection 'startups' already exists")

print("Loading data and vectors...")
# Load the startup data
fd = open("./data/startups_demo.json")
# payload is now an iterator over startup data
payload = map(json.loads, fd)

# Load all vectors into memory
vectors = np.load("./startup_vectors.npy")

print(f"Uploading {len(vectors)} vectors to Qdrant...")
# Upload the data (following tutorial exactly)
client.upload_collection(
    collection_name="startups",
    vectors=vectors,
    payload=payload,
    ids=None,  # Vector ids will be assigned automatically
    batch_size=256,  # How many vectors will be uploaded in a single request?
)

fd.close()
print("Vectors uploaded to Qdrant successfully!")
print("You can now use the 'startups' collection for neural search.")