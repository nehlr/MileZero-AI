from retrieval import get_top_chunks

def post_process_answer(raw_text):
    """
    Cleans up repetitive output loops (e.g. repeated bullet items or sentences)
    and removes duplicates while maintaining order.
    """
    if not raw_text:
        return raw_text

    lines = raw_text.strip().split('\n')
    seen = set()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Normalize for comparison (remove bullet symbols, quotes, numbers, lowercase)
        normalized = stripped.lstrip('-*•1234567890. ').strip("'\"` ").lower()
        if normalized in seen:
            # Skip repeating lines
            continue
        if len(normalized) > 0:
            seen.add(normalized)
            cleaned_lines.append(stripped)

    result = "\n".join(cleaned_lines)
    return result if result else raw_text

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
    system_prompt = (
        "You are an intelligent document Q&A assistant. "
        "Summarize the answer clearly using ONLY the provided context excerpts. "
        "Provide a unique, non-repetitive list or explanation. Do not repeat items or loop sentences. "
        "If the answer cannot be found in the context, reply: 'I don't have enough information in the documents to answer that.'"
    )
    
    user_content = (
        f"Context Excerpts:\n{context}\n\n"
        f"Question: {query}\n"
        f"Answer:"
    )

    # ---------------------------------------------------------
    # FOUNDRY LOCAL SDK / OAI UYUMLU LLM BAĞLANTISI
    # ---------------------------------------------------------
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    raw_response = ""

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
            chat_client.settings.temperature = 0.5
            chat_client.settings.max_tokens = 300
            response = chat_client.complete_chat(messages=messages)
            raw_response = response.choices[0].message.content.strip()
    except Exception as e:
        # SDK ile doğrudan model yüklenmediyse yerel server API'ye fallback yap
        pass

    if not raw_response:
        # 2. Deneme: OpenAI uyumlu yerel Foundry sunucusu (port 1234)
        try:
            from openai import OpenAI
            client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="local")
            response = client.chat.completions.create(
                model="qwen2.5-1.5b",
                messages=messages,
                temperature=0.5,
                max_tokens=300,
                presence_penalty=0.5,
                frequency_penalty=0.5
            )
            raw_response = response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM bağlantısında bir hata oluştu. Arka planda Foundry Local'ın çalıştığından ve doğru porta (örn: 1234) bağlı olduğundan emin olun. \nHata detayı: {e}"

    # Repetitive loop ve tekrar temizliği yap
    return post_process_answer(raw_response)

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
