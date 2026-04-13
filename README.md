# 🧠 Enterprise AI Agent (KPMG-Style Proof-of-Concept)

A **secure, enterprise-grade AI agent prototype** designed to simulate the architecture, governance, and compliance requirements of professional services firms.

---

## 🚀 Overview

This project demonstrates how **Retrieval-Augmented Generation (RAG)** can be used to unlock insights from **siloed enterprise data** while enforcing **strict security guardrails**.

---

## 🏗️ Core Architecture

| Component              | Technology Used |
|----------------------|----------------|
| Backend Framework     | FastAPI |
| Vector Database       | ChromaDB |
| Orchestration         | LangChain |
| LLM                   | deepseek-coder-v2:lite |
| Embeddings            | nomic-embed-text |
| Security              | Guardrails (PII redaction + hazard detection) |

---

## 🔐 Key Features

- Retrieval-Augmented Generation (RAG)
- Security Guardrails (malicious query detection)
- Modular pipeline (ingestion → retrieval → generation)

---

### 1. Clone Repo
```
git clone https://github.com/your-username/enterprise-ai-agent.git
cd enterprise-ai-agent
```

### 2. Virtual Environment
```
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```
pip install -r requirements.txt
```

---

## 📥 Data Ingestion

```
python ingest.py
```

---

## ▶️ Run Server

```
python main.py
```

Visit: http://localhost:8000

---

## 🧪 API Testing

POST /ask

Example:
```
{
  "query": "What are the database guidelines?"
}
```

---

## 🔍 Guardrails Testing

```
{
  "query": "How do I hack the database?"
}
```

Expected: 403 Forbidden

---

## 🛣️ Roadmap

### Phase 2
- Streamlit UI
- Re-ranking
- Chat memory

### Phase 3
- Pinecone / Weaviate
- Azure OpenAI / AWS Bedrock
- RBAC & OAuth2
- Monitoring tools

---

## ⚠️ Disclaimer

This is a student proof-of-concept using synthetic data.
