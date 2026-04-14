import ollama
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from guardrails.input_guardrails import redact_pii, check_intent
from guardrails.output_guardrails import scan_output_for_hazards
from langchain_core.prompts import PromptTemplate

app = FastAPI()

# Initialize Local Vector Database
client = chromadb.PersistentClient(path="./bank_code_vault")
collection = client.get_or_create_collection(name="secure_docs")

# 1. Define your Strict RAG Prompt (Updated to include your previous rules)
strict_rag_prompt = PromptTemplate.from_template(
    """You are a secure internal KPMG AI Agent for a financial institution. 
    You must adhere to the following rules:
    1. Base your answer strictly on the CONTEXT provided below.
    2. If the CONTEXT does not contain the answer, reply with: "I cannot fulfill this request based on internal documentation."
    3. Never generate code containing placeholder credentials or hardcoded secrets.
    4. Provide a brief explanation of your logic.

    CONTEXT FROM SECURE VAULT:
    {context}
    
    DEVELOPER QUESTION:
    {question}
    """
)

# 2. Define your General Knowledge Prompt
general_prompt = PromptTemplate.from_template(
    """You are a helpful AI Agent. 
    Please answer the following general knowledge question. 
    (Note: Prefix your response with 'Based on general knowledge outside of internal KPMG documentation...')
    
    Question: {question}
    Answer:"""
)

class Query(BaseModel):
    user_input: str


@app.post("/ask")
async def ask_assistant(query: Query):
    # Guardrail 1
    safe_input = redact_pii(query.user_input)
    # Guardrail 2
    check_intent(safe_input)

    try:
        # Retrieval Step: Find the most relevant local docs
        query_emb = ollama.embeddings(model="nomic-embed-text", prompt=safe_input)["embedding"]
        
        # Query ChromaDB (this returns 'documents', 'ids', and 'distances')
        results = collection.query(query_embeddings=[query_emb], n_results=2)

        # 3. Router Logic & Threshold Checking
        DISTANCE_THRESHOLD = 1.2 # Lower score = closer match in ChromaDB (L2 distance)
        relevant_docs = []

        # Check if we got results back
        if results["documents"] and results["distances"]:
            docs = results["documents"][0]
            distances = results["distances"][0]

            # Filter docs based on the threshold
            for doc, dist in zip(docs, distances):
                if dist < DISTANCE_THRESHOLD:
                    relevant_docs.append(doc)
        
        # 4. Route to the appropriate prompt
        if len(relevant_docs) == 0:
            print("Router: Low similarity scores. Routing to General Knowledge.")
            # Format the general prompt
            final_prompt = general_prompt.format(question=safe_input)
            context_used = 0
        else:
            print(f"Router: Found {len(relevant_docs)} relevant internal docs. Routing to Strict RAG.")
            # Combine the text of the relevant documents
            context_text = "\n\n".join(relevant_docs)
            # Format the strict prompt
            final_prompt = strict_rag_prompt.format(context=context_text, question=safe_input)
            context_used = len(relevant_docs)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # 5. Invoke the LLM with the dynamically chosen prompt
        output = ollama.generate(model="deepseek-coder-v2:lite", prompt=final_prompt)
        final_response = output["response"]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Model inference failed. Please try again later.")

    # Guardrail 4: output scanning
    scan_output_for_hazards(final_response)

    return {
        "status": "success",
        "redacted_input": safe_input,
        "response": final_response,
        "telemetry": {
            "context_files_used": context_used,
            "routing_path": "general_knowledge" if context_used == 0 else "strict_rag"
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app with Uvicorn on localhost
    uvicorn.run(app, host="0.0.0.0", port=8000)