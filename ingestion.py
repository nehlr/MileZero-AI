import sqlite3
import os
import json

DB_NAME = "database.db"
EMBEDDING_MODEL = "qwen3-embedding-0.6b"

# Initialize Foundry Local SDK
_embedding_client = None

def get_foundry_embedding_client():
    """
    Initializes and returns the EmbeddingClient using the official foundry-local-sdk.
    Falls back to OpenAI-compatible endpoint if standalone server is running.
    """
    global _embedding_client
    if _embedding_client is not None:
        return _embedding_client
    
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
        config = Configuration(app_name="LocalRAGAssistant")
        FoundryLocalManager.initialize(config)
        mgr = FoundryLocalManager.instance
        model = mgr.catalog.get_model(EMBEDDING_MODEL)
        if model:
            if not model.is_loaded:
                model.load()
            _embedding_client = model.get_embedding_client()
            return _embedding_client
    except Exception as e:
        print(f"[Foundry Local SDK] Direct SDK init note: {e}. Falling back to OpenAI compatible API.")
    
    # Fallback to OpenAI client pointing to local Foundry endpoint
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="local")
        return client
    except Exception as e:
        print(f"Error creating fallback client: {e}")
        return None

def init_db():
    """
    Veritabanını başlatır. Belgeleri ve onların vektörel temsillerini saklamak için 
    'documents' adında bir tablo oluşturur.
    SQLite kullanılarak veriler tamamen lokal bir dosyada tutulur.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    """
    Uzun metinleri belirli bir karakter boyutuna (chunk_size) göre parçalara böler.
    Bu parçalama (chunking) işlemi, RAG sistemlerinde LLM'in bağlam penceresini (context window)
    aşmamak ve sadece en alakalı bölümleri bulmak için kritik bir adımdır.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_embedding(text):
    """
    Verilen metni Foundry Local SDK veya yerel OpenAI API uyumlu embedding modeli ile
    sayısal bir vektöre (embedding) dönüştürür.
    """
    client = get_foundry_embedding_client()
    if client is None:
        raise RuntimeError("Foundry Local client could not be initialized.")
    
    # Check if client has generate_embedding (foundry-local-sdk EmbeddingClient)
    if hasattr(client, "generate_embedding"):
        response = client.generate_embedding(input_text=text)
        return response.data[0].embedding
    # Standard OpenAI client fallback
    elif hasattr(client, "embeddings"):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    else:
        raise RuntimeError("Unsupported embedding client type.")

def ingest_documents(doc_dir):
    """
    Belirtilen dizindeki tüm '.txt' uzantılı dosyaları okur, parçalara ayırır,
    vektörleştirir ve SQLite veritabanına kaydeder.
    """
    conn = init_db()
    cursor = conn.cursor()
    
    print(f"Embedding modeli kullanılıyor: {EMBEDDING_MODEL} (Foundry Local)...")
    
    if not os.path.exists(doc_dir):
        print(f"Klasör {doc_dir} bulunamadı.")
        return

    for filename in os.listdir(doc_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(doc_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"İşleniyor: {filename}...")
            # Metni parçalara (chunks) ayır
            chunks = chunk_text(content, chunk_size=500)
            
            for chunk in chunks:
                if not chunk.strip():
                    continue
                # Foundry Local kullanarak embedding oluştur
                vector = get_embedding(chunk)
                # SQLite, array/liste yapılarını doğrudan saklayamaz, bu yüzden JSON string'ine çeviriyoruz
                vector_json = json.dumps(vector)
                
                # Veritabanına kaydet
                cursor.execute('INSERT INTO documents (text_chunk, embedding) VALUES (?, ?)', (chunk, vector_json))
                
    conn.commit()
    conn.close()
    print("Veri aktarımı tamamlandı! Tüm belgeler vektörleştirilerek SQLite'a kaydedildi.")

if __name__ == "__main__":
    # Eğer bu betik doğrudan çalıştırılırsa, 'data' klasöründeki belgeleri işler.
    ingest_documents("data")
