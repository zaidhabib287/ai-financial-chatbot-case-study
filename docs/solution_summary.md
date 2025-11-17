AI Financial Chatbot – Case Study Solution

1. Overview

This project implements a **banking backend API** that supports:

- User registration, login, and balance management  
- Beneficiary management and money transfers  
- Daily and per-transaction limit enforcement  
- **Compliance-aware transfers** using a lightweight **RAG (Retrieval-Augmented Generation)** layer for:
  - Sanctions list checking (e.g. sanctioned countries)
  - Rules-based limit enforcement from uploaded documents  
- A simple **chat endpoint** that can answer questions using the same rules/sanctions knowledge base.

The solution is built with **FastAPI + async SQLAlchemy**, and a small, pluggable RAG subsystem that uses a local vector store.

---

2. Architecture

2.1 High-Level Components

- **API Layer (FastAPI)**
  - `backend/main.py` – app factory, middleware, routing setup
  - `backend/api/auth.py` – register/login
  - `backend/api/users.py` – user profile, balance
  - `backend/api/beneficiaries.py` – CRUD for beneficiaries
  - `backend/api/transactions.py` – transfers + limits + sanctions checks
  - `backend/api/admin.py` – admin operations (user listing, admin credit)
  - `backend/api/documents.py` – document upload, ingestion, and RAG stats/management
  - `backend/api/chatbot.py` – chat endpoint that uses the RAG manager

- **Persistence Layer**
  - `backend/models/database.py`
    - Async engine + session factory
    - SQLAlchemy `Base` for models
  - `backend/models/models.py`
    - `User`, `Beneficiary`, `Transaction`, `Document`, `ComplianceRule`, `ChatSession`, `ChatMessage`
  - `backend/models/schemas.py`
    - Pydantic models for request/response validation

- **RAG / Compliance Layer**
  - `backend/rag/rag_manager.py`
    - Orchestrates document ingestion and vector store updates
    - Parses uploaded documents (rules, sanctions, etc.)
    - Exposes `process_document()` and stats helpers
  - `rag_pipeline/vectordb/vector_store.py`
    - Simple local embedding + vector index
    - Persists store to disk under `settings.vector_db_path`

- **Configuration & Constants**
  - `backend/config/settings.py` – Pydantic settings (DB URL, paths, secrets)
  - `backend/config/constants.py`
    - Enums: `UserRole`, `TransactionType`, `TransactionStatus`, `DocumentType`
    - `SUPPORTED_DOCUMENT_EXTENSIONS`

- **Auth & Security**
  - `backend/auth/security.py` – password hashing, JWT creation/validation
  - `backend/auth/dependencies.py` – `get_current_user`, `get_admin_user`, etc.

---

3. Data Model Design

3.1 Users

- **Table**: `users`  
- **Key fields**:
  - `id: VARCHAR(36)` – UUID stored as string
  - `username`, `email` (unique)
  - `hashed_password`
  - `role: {ADMIN, CUSTOMER}`
  - `is_active: bool`
  - `daily_limit: float`
  - `balance: float`
  - `created_at`, `updated_at`

**Rationale**:  
User limits and balance live together for simpler queries. UUID identifiers keep API responses stable and opaque.

---

3.2 Beneficiaries

- **Table**: `beneficiaries`  
- **Key fields**:
  - `id`
  - `user_id` (FK → `users.id`)
  - `name`
  - `bank_name`
  - `iban`
  - `country`
  - `is_active`
  - `created_at`

Each beneficiary belongs to a customer and is used as the target in transfers.

---

3.3 Transactions

- **Table**: `transactions`  
- **Key fields**:
  - `id`
  - `sender_id` (FK → `users.id`)
  - `receiver_id` (optional, for internal transfers)
  - `beneficiary_id` (optional, for external transfers)
  - `amount`, `currency`
  - `type: {CREDIT, DEBIT, TRANSFER}`
  - `status: {PENDING, COMPLETED, FAILED, BLOCKED}`
  - `description`
  - `reference_number` (unique)
  - `created_at`, `completed_at`

This provides a full audit trail for admin credits, customer transfers, and blocked/compliance-failed attempts.

---

3.4 Documents & Compliance Rules

- **Table**: `documents`
  - `id`, `filename`, `file_path`
  - `document_type: {compliance_rules, sanctions_list, ...}`
  - `uploaded_by`
  - `file_size`
  - `is_processed`
  - `processed_at`, `created_at`

- **Table**: `compliance_rules` (conceptual)
  - Holds structured extraction results (e.g. limits, sanctions info)
  - Links back to `source_document_id`

Documents are the raw inputs; `compliance_rules` and the vector store are the structured knowledge layer used by the business logic.

---

4. RAG / Compliance Logic

4.1 Document Upload & Ingestion

**Upload endpoint**

- `POST /api/v1/admin/documents/upload`

Behavior:

- Accepts `multipart/form-data` with:
  - `document_type` (Form; `DocumentType`)
  - `file` (UploadFile)
- Validates the file extension against `SUPPORTED_DOCUMENT_EXTENSIONS`.
- Saves the file under `settings.upload_dir` with a UUID-based name.
- Inserts a `Document` row with `is_processed = False`.

**Ingestion endpoint**

- `POST /api/v1/admin/documents/ingest/{document_id}`

Behavior:

1. Loads the `Document` row from the DB.  
2. Calls `rag_manager.process_document()` with:
   - `file_path`
   - `document_id`
   - `document_type`
3. Updates `is_processed = True` and sets `processed_at = datetime.utcnow()`.

---

4.2 Vector Store & Stats

The vector store keeps embeddings of processed chunks (rules, sanctions, etc.).

- **Populate / update index**  
  - Triggered via `POST /ingest/{document_id}`.
  - `rag_manager.process_document()`:
    - Reads file content.
    - Chunks and embeds text.
    - Stores vectors keyed by `source = document_id`.

- **Stats endpoint**  
  - `GET /api/v1/admin/documents/rag/stats`  
  - Returns aggregated info such as:
    - `total_documents`
    - `total_chunks`
    - `by_document_type`

- **Delete by source**  
  - `DELETE /api/v1/admin/documents/rag/delete-by-source/{document_id}`

---

4.3 Applying RAG in Business Logic

**Sanctions check**

- Query vector store using beneficiary attributes (primarily `country`).
- If match indicates sanctioned entity → block transfer and record `status = BLOCKED`.

**Limits from rules documents**

- Rules like:
  > “Daily transfer limit is 1000 BHD. Per transaction limit is 500 BHD.”
- Extracted via RAG and enforced in transaction validation.

---

5. Core API Flows

5.1 Registration & Login

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

5.2 Balance & Limits

- `GET /api/v1/users/profile`
- `GET /api/v1/users/balance`

5.3 Beneficiaries

- `POST /api/v1/beneficiaries/`
- `GET /api/v1/beneficiaries/`

5.4 Transfers

- `POST /api/v1/transactions/transfer`

Validation order:

1. Balance check  
2. Per-transaction limit  
3. Daily limit  
4. Sanctions check via RAG  

---

6. Error Handling & Logging

- Central exception handler in `backend/main.py`
- Async DB transactions with explicit commit/rollback
- Logging configured with persistent log file

---

7. Security Considerations

- JWT authentication (HS256)
- Bcrypt password hashing
- Role-based authorization
- Environment variable-based config

---

8. Run Instructions

8.1 Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./data/app.db"
uvicorn backend.main:app --reload
```

8.2 Run Tests

```bash
pytest -q
```

---

9. Assumptions & Limitations

- Simplified sanctions detection
- Simple RAG implementation  
- Single-currency (BHD) assumption  
- Date boundaries assume server timezone

---

10. Future Enhancements

- Full UI dashboard  
- Smarter rule extraction (ML/LLM based)  
- External sanctions/KYC APIs  
- Multi-currency & region-aware limits  

