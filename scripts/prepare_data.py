from sentence_transformers import SentenceTransformer
import numpy as np
import json
import pandas as pd
from tqdm import tqdm

print("Loading SentenceTransformer model...")
# You will be using a pre-trained model called all-MiniLM-L6-v2
model = SentenceTransformer(
    "all-MiniLM-L6-v2", device="cpu"  # or device="cuda" if you have GPU
)

print("Reading startup data...")
# Read the raw data file
df = pd.read_json("./data/startups_demo.json", lines=True)

print(f"Found {len(df)} startups in the dataset")
print("Sample data:")
print(df.head(2))

print("\nEncoding all startup descriptions...")
# Encode all startup descriptions to create an embedding vector for each
vectors = model.encode(
    [row.alt + ". " + row.description for row in df.itertuples()],
    show_progress_bar=True,
)

print(f"Created {vectors.shape[0]} vectors of {vectors.shape[1]} dimensions")

# Save vectors to file
print("Saving vectors to startup_vectors.npy...")
np.save("startup_vectors.npy", vectors, allow_pickle=False)

print("Data preparation complete!")
print("Files created:")
print("- startup_vectors.npy (vector embeddings)")
print("- Original data is in data/startups_demo.json")