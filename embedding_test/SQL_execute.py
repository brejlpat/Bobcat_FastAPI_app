import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# User input
user_input = input("Enter a machine description or name: ").strip()
user_vector = model.encode([user_input])[0]  # Get vector

# Connect to the DB
conn = sqlite3.connect(r"C:\Users\patrikbrejla\Documents\vector\channels_embedding.db")
cur = conn.cursor()

# Load all machine names and vectors
cur.execute("SELECT name, vector FROM embeddings")
rows = cur.fetchall()

# Calculate cosine similarities
names = []
vectors = []

for name, vector_str in rows:
    vector = np.array(json.loads(vector_str))
    names.append(name)
    vectors.append(vector)

vectors = np.vstack(vectors)
similarities = cosine_similarity([user_vector], vectors)[0]

# Get top 5 matches
top_indices = similarities.argsort()[-5:][::-1]

print("\nTop 5 closest matches:")
for idx in top_indices:
    print(f"{names[idx]} (similarity: {similarities[idx]:.4f})")

conn.close()
