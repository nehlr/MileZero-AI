import sqlite3
import os
import json

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create table for documents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_chunk TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

def chunk_text(text, chunk_size=500):
    # Simple chunking by character length
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def ingest_documents(doc_dir):
    conn = init_db()
    cursor = conn.cursor()
    
    # Initialize your Foundry Local embedding model here
    # e.g., from foundry_local import EmbeddingModel
    # embedder = EmbeddingModel("qwen3-embedding-0.6b")
    
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
        print(f"Created directory {doc_dir}. Please add some text files there and run this again.")
        return

    for filename in os.listdir(doc_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(doc_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                chunks = chunk_text(text)
                
                for chunk in chunks:
                    # TODO: generate actual embedding
                    # embedding = embedder.embed(chunk)
                    # For now, we store a mock embedding
                    mock_embedding = [0.0] * 128
                    
                    cursor.execute(
                        "INSERT INTO documents (text_chunk, embedding) VALUES (?, ?)",
                        (chunk, json.dumps(mock_embedding))
                    )
    conn.commit()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_documents("data")
