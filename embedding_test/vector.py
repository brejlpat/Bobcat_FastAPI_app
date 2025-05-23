import sqlite3
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Read lines from a file
with open(r"C:\Users\patrikbrejla\Documents\vector\channel_names.txt") as f:
    lines = [line.strip() for line in f if line.strip()]

# Generate embeddings
embeddings = model.encode(lines)

# Connect to SQLite and create table
conn = sqlite3.connect(r"C:\Users\patrikbrejla\Documents\vector\channels_embedding.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        vector TEXT  -- Store the vector as a JSON string
    )
""")

# Insert each line and its vector
for name, vector in zip(lines, embeddings):
    vector_str = json.dumps(vector.tolist())  # Convert NumPy array to JSON string
    cur.execute("INSERT INTO embeddings (name, vector) VALUES (?, ?)", (name, vector_str))

conn.commit()
conn.close()

print("✅ Embeddings saved to 'machine_embeddings.db'")
