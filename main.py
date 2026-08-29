from retrieval import get_top_chunks

def answer_query(query):
    """
    Retrieves context from the local database and sends it to the local LLM to generate an answer.
    """
    # 1. Retrieve the most relevant chunks from SQLite
    chunks = get_top_chunks(query, top_k=3)
    
    if not chunks:
        return "I don't have enough information in my local documents to answer that."

    # Combine the chunks into a single context string
    context = "\n\n".join([f"Source Chunk:\n{c}" for c in chunks])

    # 2. Prepare the prompt for the local LLM
    # In a real scenario, you use Foundry Local's SDK or an OpenAI-compatible client here.
    system_prompt = (
        "You are a helpful local assistant. Answer the user's question using ONLY the "
        "information provided in the context below. If you don't find the answer in the "
        "context, just say 'I don't know'. Do not hallucinate or use outside knowledge."
    )
    
# ---------------------------------------------------------
    # FOUNDRY LOCAL SDK / OAI UYUMLU LLM BAĞLANTISI
    # ---------------------------------------------------------
    messages = [
        # System prompt: Modelin nasıl davranması gerektiğini (Rolünü) ve kısıtlamalarını belirtir.
        {"role": "system", "content": system_prompt + "\n\nContext:\n" + context},
        # User prompt: Kullanıcının gerçek sorusudur.
        {"role": "user", "content": query}
    ]

    # 1. Deneme: Doğrudan foundry-local-sdk ChatClient kullanımı
    try:
        from foundry_local_sdk import Configuration, FoundryLocalManager
        config = Configuration(app_name="LocalRAGAssistant")
        FoundryLocalManager.initialize(config)
        mgr = FoundryLocalManager.instance
        model = mgr.catalog.get_model("qwen2.5-1.5b")
        if model:
            if not model.is_loaded:
                model.load()
            chat_client = model.get_chat_client()
            chat_client.settings.temperature = 0.1
            response = chat_client.complete_chat(messages=messages)
            return response.choices[0].message.content
    except Exception as e:
        # SDK ile doğrudan model yüklenmediyse yerel server API'ye fallback yap
        pass

    # 2. Deneme: OpenAI uyumlu yerel Foundry sunucusu (port 1234)
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="local")
        response = client.chat.completions.create(
            model="qwen2.5-1.5b",
            messages=messages,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM bağlantısında bir hata oluştu. Arka planda Foundry Local'ın çalıştığından ve doğru porta (örn: 1234) bağlı olduğundan emin olun. \nHata detayı: {e}"

def main():
    print("========================================")
    print(" Welcome to Local RAG AI Assistant (CLI)")
    print(" Type 'exit' or 'quit' to stop.")
    print("========================================\n")
    
    # Run the interactive Q&A loop
    while True:
        try:
            user_question = input("Your question: ").strip()
            if user_question.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if not user_question:
                continue

            print("Retrieving context and generating answer...\n")
            answer = answer_query(user_question)
            
            print(f"🤖 Assistant:\n{answer}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
