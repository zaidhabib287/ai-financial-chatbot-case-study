# System Architecture

## Overview
The AI-Powered Financial Chatbot System consists of multiple components working together to provide secure fund transfer capabilities with compliance checking through RAG-based document processing.

## High-Level Architecture
┌─────────────────┐     ┌─────────────────┐
│   Chatbot UI    │     │  Admin Portal   │
└────────┬────────┘     └────────┬────────┘
│                       │
├───────────┬───────────┤
│
┌──────┴──────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
│
┌───────────────┼───────────────┐
│               │               │
┌────┴────┐    ┌────┴────┐    ┌────┴────┐
│Database │    │  Redis  │    │Vector DB│
│  (PG)   │    │ (Cache) │    │ (FAISS) │
└─────────┘    └─────────┘    └─────────┘

## Components

### 1. Frontend Layer
- **Chatbot UI**: React-based interface for customer interactions
- **Admin Portal**: Streamlit-based dashboard for administrators

### 2. API Layer
- **FastAPI Backend**: RESTful API handling all business logic
- **Authentication**: JWT-based authentication for secure access
- **Mock APIs**: Simulated banking APIs for testing

### 3. Processing Layer
- **RAG Pipeline**: Document ingestion and embedding generation
- **Langchain**: LLM orchestration for chatbot intelligence
- **Compliance Engine**: Rule validation and sanctions checking

### 4. Data Layer
- **PostgreSQL**: Primary database for user data and transactions
- **Redis**: Caching and session management
- **FAISS**: Vector database for semantic search

## Data Flow

### Fund Transfer Flow
1. User initiates transfer through chatbot
2. Chatbot validates user authentication
3. System checks beneficiary against sanctions list (RAG)
4. Balance verification through mock API
5. Compliance rules checked from vector DB
6. Transaction executed if all checks pass
7. Transaction logged in database

### Document Ingestion Flow
1. Admin uploads compliance document
2. Document parsed and chunked
3. Embeddings generated for chunks
4. Vectors stored in FAISS
5. Rules extracted and stored in database

## Security Measures
- JWT token-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Secure password hashing (bcrypt)
- API rate limiting

## Scalability Considerations
- Stateless API design
- Redis for caching frequently accessed data
- Asynchronous processing for document ingestion
- Database connection pooling
- Containerized deployment with Docker