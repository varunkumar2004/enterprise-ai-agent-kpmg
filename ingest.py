import os
import uuid
import ollama
import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

"""This script is used to ingest local documents into the secure vault. Run this once to "seed" your data."""
client = chromadb.PersistentClient(path="./bank_code_vault")
collection = client.get_or_create_collection(name="secure_docs")

def ingest_documents():
    print("loading documents from ./data directory...")

    """Load documents from the local directory"""
    loader = DirectoryLoader("./data", glob="**/*.md", show_progress=True, loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("No documents found in the specified directory.")
        return
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, # tokens/chars per chunk
        chunk_overlap=50 # overlap to maintain context btw chunks
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Generated {len(chunks)} chunks from the original documents.")

    """Ingest chunks into the local vector database"""
    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        text_content = chunk.page_content

        response = ollama.embeddings(model="nomic-embed-text", prompt=text_content)

        collection.add(
            ids=[doc_id], 
            embeddings=[response["embedding"]], 
            documents=[text_content],
            metadatas=[{"source": chunk.metadata.get("source", "unknown")}]
        )

    print("Ingestion complete. Knowlegde base seeded.")

if __name__ == "__main__":
    ingest_documents()

