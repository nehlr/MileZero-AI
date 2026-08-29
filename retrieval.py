import sqlite3
import json
import numpy as np

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

def get_embedding(text):
    """
    Kullanıcının sorusunu, belgeleri vektörleştirirken kullandığımız aynı model ile 
    (Foundry Local SDK veya yerel OpenAI uyumlu endpoint üzerinden) sayısal bir vektöre dönüştürür.
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

def cosine_similarity(vec1, vec2):
    """
    İki vektör arasındaki kosinüs benzerliğini hesaplar.
    Bu matematiksel formül, iki cümlenin (vektörün) anlamsal olarak birbirine ne kadar
    benzediğini 0 ile 1 arasında bir skorla ölçmemizi sağlar.
    RAG sistemlerinin kalbindeki temel 'arama/retrieval' algoritması budur.
    """
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def get_top_chunks(query, top_k=3):
    """
    Kullanıcının sorusuna en alakalı olan 'top_k' adet metin parçasını (chunk)
    SQLite veritabanından bularak geri döndürür.
    """
    # 1. Kullanıcı sorusunu embedding vektörüne çevir
    query_vector = get_embedding(query)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 2. Veritabanındaki tüm metin parçalarını ve önceden hesaplanmış vektörlerini al
    cursor.execute('SELECT text_chunk, embedding FROM documents')
    rows = cursor.fetchall()
    conn.close()
    
    scored_chunks = []
    for row in rows:
        text_chunk = row[0]
        # JSON olarak saklanan embedding'i tekrar Python listesine (numpy dizisine) dönüştür
        doc_vector = np.array(json.loads(row[1]))
        
        # 3. Soru vektörü ile döküman vektörü arasındaki kosinüs benzerliğini hesapla
        sim = cosine_similarity(query_vector, doc_vector)
        scored_chunks.append((sim, text_chunk))
        
    # 4. Benzerlik skoruna göre büyükten küçüğe sırala ve en yüksek skora sahip parçaları al
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for sim, chunk in scored_chunks[:top_k]]
    
    return top_chunks
