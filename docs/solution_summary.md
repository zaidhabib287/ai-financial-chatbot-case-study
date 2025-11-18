# Solution Summary - AI Financial Chatbot Case Study

This document provides a complete overview of the AI-powered financial chatbot system with compliance-aware rules, LLM-based conversational interface, and RAG (Retrieval-Augmented Generation) support.

---

## 1. Project Overview

This project implements a fully working **AI-powered financial assistant** capable of:

- Secure banking-like APIs for user registration, login, balance, and transfers
- Beneficiary management with country validation
- **Compliance checking using RAG-based document ingestion**
- **LLM-powered chatbot using Streamlit UI** with fallback behavior
- Seamless integration between backend REST APIs, vector DB, and LLM engine

It combines knowledge-driven rules with AI conversational capabilities while ensuring secure financial transactions.

---

## 2. System Architecture

### High-Level Components

| Layer | Component | Description |
|--------|----------------|--------------|
| Frontend | Streamlit Chat UI | Auth-enabled conversational client |
| Backend | FastAPI | REST APIs for authentication, transfers, RAG ingestion, chatbot |
| Data | SQLite (default), can scale to PostgreSQL | Persistent storage |
| Vector DB | Local Vector Index | Embeddings + semantic search |
| AI Engine | Ollama (Local Model), Fallback Bot | Chat response generation |

Architecture Diagram:

```
User → Streamlit Chat UI → FastAPI Backend → LLM Engine / RAG → Response
                                               |
                                               → Vector DB + Documents
```

---

## 3. RAG Workflow

1. Admin uploads compliance or sanctions documents  
2. Backend ingests and chunks text  
3. Embeddings are stored in vector DB  
4. During transfer/chat, semantic search retrieves relevant rules  
5. Response/decision incorporates contextual rules  

---

## 4. Chatbot Behavior

| Mode | Source | Use Case |
|---------|------------------------|------------------------------|
| Primary | Local LLM via Ollama | Dynamic natural chat |
| Secondary | Knowledge Base (RAG) | Rules, sanctions, compliance |
| Fallback | Hardcoded responses | When LLM unavailable |

JWT Authentication is required for chat usage.

---

## 5. Compliance & Transaction Rules

Validation Sequence:

1. Account balance check  
2. Per transaction limit  
3. Daily transfer limit  
4. Sanctions/RAG rule check  

If any rule fails → **transaction is blocked**.

---

## 6. How to Run

### Backend

```bash
cd backend
uvicorn main:app --reload
```

### Ensure LLM is Running

```bash
ollama pull gemma3:4b
```

### Frontend Chat UI

```bash
cd frontend/chatbot-ui
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 7. Testing

```bash
pytest -q
```

---

## 8. Future Enhancements

- Multi-currency & FX support
- Fine-tuned compliance extraction model
- Kubernetes & Cloud deployment
- Production-grade monitoring

---

## Status

**Version: Final Submitted (LLM + RAG + UI + Tests + Docs)**


