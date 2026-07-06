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
    # TODO: Replace the mock response below with the real Foundry Local SDK call:
    # ---------------------------------------------------------
    # Example using OpenAI-compatible Foundry Local client:
    # from openai import OpenAI
    # client = OpenAI(base_url="http://localhost:1234/v1", api_key="local")
    # response = client.chat.completions.create(
    #     model="phi-1.5-mini",
    #     messages=[
    #         {"role": "system", "content": system_prompt + "\n\nContext:\n" + context},
    #         {"role": "user", "content": query}
    #     ]
    # )
    # return response.choices[0].message.content
    
    mock_response = f"[Mock LLM] Based on the {len(chunks)} chunks retrieved from the local database, here is the answer to your question: '{query}'. \n(Replace this with real LLM inference code)."
    return mock_response

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
