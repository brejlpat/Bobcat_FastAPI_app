import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to DB and load data once
conn = sqlite3.connect(r"C:\Users\pavelchuman\Documents\vector\channels_embedding.db")
cur = conn.cursor()
cur.execute("SELECT name, vector FROM embeddings")
rows = cur.fetchall()
conn.close()

# Extract names and vectors
names, vectors = [], []
for name, vector_str in rows:
    vector = np.array(json.loads(vector_str))
    names.append(name)
    vectors.append(vector)
vectors = np.vstack(vectors)

# Start input loop
print("🔁 Type a machine description (or 'exit' to quit):")
while True:
    user_input = input("\n> ").strip()
    if user_input.lower() in {"exit", "quit"}:
        print("👋 Exiting.")
        break

    # Semantic vector
    user_vector = model.encode([user_input])[0]
    similarities = cosine_similarity([user_vector], vectors)[0]

    # Semantic matching
    threshold = 0.4
    matching_indices = [i for i, score in enumerate(similarities) if score > threshold]

    if matching_indices:
        matching_indices.sort(key=lambda i: similarities[i], reverse=True)
        print(f"\n✅ Semantic matches with similarity > {threshold}:")
        for idx in matching_indices:
            print(f"{names[idx]} (similarity: {similarities[idx]:.4f})")
    else:
        print(f"\n⚠️ No semantic matches above {threshold}. Trying fuzzy match...")

        fuzzy_scores = [(name, fuzz.partial_ratio(user_input.lower(), name.lower())) for name in names]
        fuzzy_matches = [(name, score) for name, score in fuzzy_scores if score >= 70]
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)

        if fuzzy_matches:
            print("\n🔍 Fuzzy keyword matches (score ≥ 70):")
            for name, score in fuzzy_matches[:5]:
                print(f"{name} (fuzzy score: {score})")
        else:
            print("❌ No fuzzy keyword matches found.")
