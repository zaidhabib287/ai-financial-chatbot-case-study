import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.dependencies import get_admin_user
from backend.config.constants import SUPPORTED_DOCUMENT_EXTENSIONS, DocumentType
from backend.config.settings import settings
from backend.models.database import get_db
from backend.models.models import Document, User
from backend.models.schemas import DocumentUploadResponse
from backend.rag.rag_manager import rag_manager  # Phase 3 manager

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only document upload endpoint.

    - Validates extension
    - Saves file under a UUID filename (id + ext)
    - Stores DB record
    - Returns a minimal response used by tests and frontend:
        { "success": true, "document_id": "<uuid>", "filename": "rules.txt" }
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Save file
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    doc_id = uuid4()
    saved_path = os.path.join(upload_dir, f"{doc_id}{ext}")

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    # Persist Document row
    db_doc = Document(
        id=doc_id,
        filename=file.filename,
        file_path=saved_path,
        document_type=document_type,
        uploaded_by=admin.id,
        file_size=len(content),
        is_processed=False,
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    # Important: only return basic info, as per response_model
    return DocumentUploadResponse(
        success=True,
        document_id=str(doc_id),
        filename=file.filename,
    )


@router.post("/ingest/{document_id}")
async def ingest_document(
    document_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger Phase-3 RAG ingestion for a given document.

    Uses the document_id returned from /upload.
    """
    # Load Document
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Run Phase-3 RAG processing
    out = await rag_manager.process_document(
        file_path=doc.file_path,
        document_id=str(doc.id),
        document_type=str(doc.document_type.value),
    )  # returns rules/sanctions/stats per Phase 3

    # Mark processed
    doc.is_processed = True
    doc.processed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(doc)

    return {"success": True, "processing": out}


@router.get("/list")
async def list_documents(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents in reverse chronological order.
    """
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "type": d.document_type.value,
            "size": d.file_size,
            "processed": d.is_processed,
            "created_at": d.created_at,
            "processed_at": d.processed_at,
        }
        for d in docs
    ]


@router.get("/rag/stats")
async def rag_stats(admin: User = Depends(get_admin_user)):
    """
    Return vector-store / RAG statistics.
    """
    return rag_manager.vector_store.get_stats()


@router.delete("/rag/delete-by-source/{document_id}")
async def rag_delete_by_source(
    document_id: str,
    admin: User = Depends(get_admin_user),
):
    """
    Remove all vectors associated with a given document source id from the vector store.
    """
    deleted = rag_manager.vector_store.delete_by_source(document_id)
    rag_manager.vector_store.save()
    return {"success": True, "deleted_vectors": deleted}
