# AI-Powered Financial Chatbot System

A secure, rule-driven chatbot system for fund transfers and beneficiary management with **RAG-based compliance validation** and **LLM-powered conversational UI**.

---

## 🚀 Key Features

- Customer chatbot (LLM + RAG enabled)
- Beneficiary & fund-transfer workflow
- Compliance-rule validation + sanctions safety
- Admin document ingestion + vector database
- Streamlit chat UI with JWT authentication
- Local LLM integration via **Ollama**
- Full test suite using `pytest`

---

## 🧠 Tech Stack

| Area | Tools |
|----------|----------------|
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM Engine | Ollama (Local), fallback |
| RAG | Local vector DB |
| DB | SQLite (default), ready for PostgreSQL |
| Auth | JWT |
| Testing | Pytest |

---

## 📄 Documentation

| File | Description |
|-------------------------|----------------------|
| `docs/solution_summary.md` | Full case study solution |
| `docs/setup.md` | Setup instructions |
| `docs/architecture/system-design.md` | Architecture blueprint |

---

## 🏁 How to Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Start LLM:

```bash
ollama pull gemma3:4b
```

Start Chat UI:

```bash
cd frontend/chatbot-ui
streamlit run app.py
```

---


