import asyncio
import os
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.dependencies import get_admin_user
from backend.config.constants import DocumentType  # <-- use the enum
from backend.config.constants import (
    SUPPORTED_DOCUMENT_EXTENSIONS,
    TransactionStatus,
    TransactionType,
)
from backend.config.settings import settings
from backend.models.database import get_db
from backend.models.models import Document, Transaction, User
from backend.models.schemas import AccountOperation
from backend.models.schemas import Document as DocumentSchema
from backend.models.schemas import MockApiResponse
from backend.models.schemas import User as UserSchema
from backend.rag.rag_manager import (  # Phase-3 RAG manager (vector_store lives here)
    rag_manager,
)
from backend.utils.mock_apis import generate_reference_number

router = APIRouter()


# ---- Background processing helpers ----
def _dispatch_rag_processing(file_path: str, document_id: str, document_type: str):
    """
    Sync wrapper for background task that schedules the async RAG processing.
    """

    async def _run():
        # document_type here is a string; RAGManager expects a string too per Phase-3
        result = await rag_manager.process_document(
            file_path, document_id, document_type
        )  # :contentReference[oaicite:2]{index=2}
        if result.get("success"):
            print(
                f"[RAG] Document {document_id} processed: {result['processing_stats']}"
            )
        else:
            print(
                f"[RAG] Document {document_id} processing failed: {result.get('error')}"
            )

    # Schedule the coroutine on the event loop after response is sent
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(_run())
    except RuntimeError:
        # if no loop is running (unlikely under FastAPI), fallback
        asyncio.run(_run())


@router.post("/documents/upload", response_model=DocumentSchema)
async def upload_document(
    # Accept as form field when using multipart/form-data with file upload
    document_type: DocumentType = Form(...),  # <-- enum validation
    background_tasks: BackgroundTasks = None,
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a compliance document and kick off background ingestion into RAG."""
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Supported types: {SUPPORTED_DOCUMENT_EXTENSIONS}",
        )

    # Check file size
    contents = await file.read()
    file_size = len(contents)
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_upload_size} bytes",
        )

    # Use a real UUID for model (UUID(as_uuid=True))
    document_uuid = uuid4()
    unique_filename = f"{document_uuid}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    # Save file
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create document record (document_type is Enum -> store enum)
    document = Document(
        id=document_uuid,
        filename=file.filename,
        file_path=file_path,
        document_type=document_type,
        uploaded_by=admin_user.id,
        file_size=file_size,
        is_processed=False,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Kick off background ingestion into vector DB (Phase-3 pipeline):contentReference[oaicite:3]{index=3}
    if background_tasks is not None:
        # Use a sync wrapper that schedules the async work
        background_tasks.add_task(
            _dispatch_rag_processing,
            file_path,
            str(document_uuid),
            document_type.value,
        )
    else:
        # Fallback: process inline (await). Comment out if you prefer only background.
        await rag_manager.process_document(
            file_path, str(document_uuid), document_type.value
        )

    return document


@router.get("/documents", response_model=List[DocumentSchema])
async def list_documents(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all uploaded documents"""
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    )
    documents = result.scalars().all()
    return documents


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its embeddings (RAG vectors)."""
    # Get document
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from vector store (Phase-3 VectorStore supports delete_by_source):contentReference[oaicite:4]{index=4}
    deleted = rag_manager.vector_store.delete_by_source(str(document_id))
    rag_manager.vector_store.save()

    # Delete from database
    await db.delete(document)
    await db.commit()

    return {
        "message": "Document deleted successfully",
        "embeddings_deleted": deleted,
    }


@router.get("/rag/stats")
async def get_rag_stats(
    admin_user: User = Depends(get_admin_user),
):
    """Get RAG system statistics (from vector store)."""
    return rag_manager.vector_store.get_stats()  # :contentReference[oaicite:5]{index=5}


@router.post("/users/{user_id}/credit", response_model=MockApiResponse)
async def credit_user_account(
    user_id: str,
    operation: AccountOperation,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Credit user account (admin only)."""
    if operation.operation_type != "credit":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid operation type for this endpoint",
        )

    # Get user
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update balance
    user.balance += operation.amount

    # Create transaction record
    transaction = Transaction(
        sender_id=admin_user.id,
        receiver_id=user.id,
        amount=operation.amount,
        currency="BHD",
        type=TransactionType.CREDIT,
        status=TransactionStatus.COMPLETED,
        description=operation.description or "Account credit by admin",
        reference_number=generate_reference_number("CREDIT"),
        completed_at=datetime.utcnow(),
    )

    db.add(transaction)
    await db.commit()

    return MockApiResponse(
        success=True,
        message="Account credited successfully",
        data={
            "user_id": str(user_id),
            "amount": operation.amount,
            "new_balance": user.balance,
            "reference": transaction.reference_number,
        },
    )


@router.post("/users/{user_id}/debit", response_model=MockApiResponse)
async def debit_user_account(
    user_id: str,
    operation: AccountOperation,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Debit user account (admin only)."""
    if operation.operation_type != "debit":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid operation type for this endpoint",
        )

    # Get user
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check balance
    if user.balance < operation.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    # Update balance
    user.balance -= operation.amount

    # Create transaction record
    transaction = Transaction(
        sender_id=user.id,
        receiver_id=admin_user.id,
        amount=operation.amount,
        currency="BHD",
        type=TransactionType.DEBIT,
        status=TransactionStatus.COMPLETED,
        description=operation.description or "Account debit by admin",
        reference_number=generate_reference_number("DEBIT"),
        completed_at=datetime.utcnow(),
    )

    db.add(transaction)
    await db.commit()

    return MockApiResponse(
        success=True,
        message="Account debited successfully",
        data={
            "user_id": str(user_id),
            "amount": operation.amount,
            "new_balance": user.balance,
            "reference": transaction.reference_number,
        },
    )


@router.get("/users", response_model=List[UserSchema])
async def list_all_users(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all users with details (admin only)."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/stats", response_model=dict)
async def get_system_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system statistics (admin only)."""
    # Total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()

    # Total transactions
    transactions_result = await db.execute(select(func.count(Transaction.id)))
    total_transactions = transactions_result.scalar()

    # Total volume
    volume_result = await db.execute(
        select(func.sum(Transaction.amount)).filter(
            Transaction.status == TransactionStatus.COMPLETED
        )
    )
    total_volume = volume_result.scalar() or 0.0

    # Today's transactions
    today = func.date(func.now())
    today_result = await db.execute(
        select(func.count(Transaction.id)).filter(
            func.date(Transaction.created_at) == today
        )
    )
    today_transactions = today_result.scalar()

    # Vector store stats (Phase-3):contentReference[oaicite:6]{index=6}
    rag_stats = rag_manager.vector_store.get_stats()

    return {
        "total_users": total_users,
        "total_transactions": total_transactions,
        "total_volume": total_volume,
        "today_transactions": today_transactions,
        "currency": "BHD",
        "rag_system": rag_stats,
    }
