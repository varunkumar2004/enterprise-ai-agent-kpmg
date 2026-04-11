import ollama
import chromadb
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 1. Initialize Local Vector Database
client = chromadb.PersistentClient(path="./bank_code_vault")
collection = client.get_or_create_collection(name="secure_docs")


class Query(BaseModel):
    user_input: str


# 2. Function to add local documents (Run this once to "seed" your data)
def seed_knowledge_base(text_content, doc_id):
    # Generates a numerical representation for search
    response = ollama.embeddings(model="nomic-embed-text", prompt=text_content)
    collection.add(
        ids=[doc_id], embeddings=[response["embedding"]], documents=[text_content]
    )


@app.post("/ask")
async def ask_assistant(query: Query):
    # 3. Retrieval Step: Find the most relevant local docs
    query_emb = ollama.embeddings(model="nomic-embed-text", prompt=query.user_input)[
        "embedding"
    ]
    results = collection.query(query_embeddings=[query_emb], n_results=2)
    context = "\n".join(results["documents"][0])

    # 4. Augmentation & Generation: Prompt Enrichment
    prompt = f"""
    You are a secure Bank Coding Assistant. Use the context below to help the developer.
    CONTEXT FROM PRIVATE REPO:
    {context}
    
    USER QUESTION:
    {query.user_input}
    """

    # 5. Model Inference using DeepSeek-Coder-V2 Lite
    output = ollama.generate(model="deepseek-coder-v2:lite", prompt=prompt)

    return {"response": output["response"], "context_used": context}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
