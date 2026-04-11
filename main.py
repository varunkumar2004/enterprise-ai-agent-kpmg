import ollama
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from guardrails.input_guardrails import redact_pii, check_intent
from guardrails.output_guardrails import scan_output_for_hazards

app = FastAPI()

"""Initialize Local Vector Database"""
client = chromadb.PersistentClient(path="./bank_code_vault")
collection = client.get_or_create_collection(name="secure_docs")


class Query(BaseModel):
    user_input: str


"""Function to add local documents (Run this once to "seed" your data)"""
def seed_knowledge_base(text_content, doc_id):
    """Generates a numerical representation for search"""
    response = ollama.embeddings(model="nomic-embed-text", prompt=text_content)
    collection.add(ids=[doc_id], embeddings=[response["embedding"]], documents=[text_content])


@app.post("/ask")
async def ask_assistant(query: Query):
    """Guardrail 1"""
    safe_input = redact_pii(query.user_input)
    """Guardrail 2"""
    check_intent(safe_input)

    try:
        """Retrieval Step: Find the most relevant local docs"""
        query_emb = ollama.embeddings(model="nomic-embed-text", prompt=safe_input)["embedding"]
        results = collection.query(query_embeddings=[query_emb], n_results=2)

        """handling empty vault scenario"""
        if results["documents"] and results["documents"][0]:
            context = "\n".join(results["documents"][0])
        else: 
            context = "No internal documentation found for this query."

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    """Guardrail 3"""
    prompt = f"""
    You are a secure internal coding assistant for a financial institution. 
    You must adhere to the following rules:
    1. Base your answer strictly on the CONTEXT provided below.
    2. If the CONTEXT does not contain the answer, reply with: "I cannot fulfill this request based on internal documentation."
    3. Never generate code containing placeholder credentials or hardcoded secrets.
    4. Provide a brief explanation of your logic.

    CONTEXT FROM SECURE VAULT:
    {context}
    
    DEVELOPER QUESTION:
    {safe_input}
    """

    try:
        output = ollama.generate(model="deepseek-coder-v2:lite", prompt=prompt)
        final_response = output["response"]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Model inference failed. Please try again later.")

    """Guardrail 4: output scanning"""
    scan_output_for_hazards(final_response)

    return {
        "status": "success",
        "redacted_input": safe_input,
        "response": final_response,
        "telemetry": {"context_files_used": len(results["documents"][0]) if results["documents"] else 0}
    }


if __name__ == "__main__":
    import uvicorn

    """Run the FastAPI app with Uvicorn on localhost"""
    uvicorn.run(app, host="0.0.0.0", port=8000)
