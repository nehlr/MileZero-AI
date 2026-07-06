import sqlite3
import json
import math

DB_NAME = "database.db"

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def get_top_chunks(query, top_k=3):
    # TODO: embed query using the same Foundry Local embedding model
    # e.g., query_embedding = embedder.embed(query)
    # Using mock embedding for now:
    query_embedding = [0.0] * 128
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT text_chunk, embedding FROM documents")
    
    results = []
    for row in cursor.fetchall():
        text_chunk = row[0]
        embedding = json.loads(row[1])
        similarity = cosine_similarity(query_embedding, embedding)
        results.append((similarity, text_chunk))
        
    conn.close()
    
    # Sort by highest similarity
    results.sort(key=lambda x: x[0], reverse=True)
    return [chunk for sim, chunk in results[:top_k]]

if __name__ == "__main__":
    query = "What is RAG?"
    chunks = get_top_chunks(query)
    print("Top chunks retrieved:")
    for c in chunks:
        print("-", c)
