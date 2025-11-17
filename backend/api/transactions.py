from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.dependencies import get_current_active_user
from backend.config.constants import TransactionStatus, TransactionType
from backend.config.settings import settings
from backend.models.database import get_db
from backend.models.models import Beneficiary, Transaction, User
from backend.models.schemas import TransactionResponse, TransferRequest
from backend.rag.rag_manager import rag_manager
from backend.utils.mock_apis import generate_reference_number, mock_banking_api

router = APIRouter()


async def validate_transfer(
    amount: float,
    user: User,
    beneficiary: Beneficiary,
    db: AsyncSession,
) -> tuple[bool, Optional[str]]:
    """
    Validate a transfer request using:
    - Current balance
    - Per-transaction & daily limits (settings + RAG overrides)
    - Sanctions check (mock API + RAG-extracted lists)
    """
    # 0) Quick balance
    if user.balance < amount:
        return False, "Insufficient balance"

    # ---------- RAG LOOKUPS (limits + sanctions) ----------
    # Build compact queries to retrieve relevant chunks from FAISS
    # (Phase 3 provides EmbeddingGenerator + VectorStore; we reuse both):contentReference[oaicite:2]{index=2}
    try:
        # Compose a small helper to query vector store and parse with RuleExtractor
        async def _rag_limits_and_sanctions():
            # queries focus each concept so we get the best chunks per topic
            queries = [
                "daily transfer limit in BHD for customers",
                "per transaction limit in BHD for single transfer",
                "sanctioned or blacklisted countries list",
                "sanctioned individuals or entities list",
            ]

            extracted_rules = []
            sanctions = {"countries": set(), "entities": set()}

            for q in queries:
                q_emb = rag_manager.embedding_generator.generate_single_embedding(
                    q
                )  # :contentReference[oaicite:3]{index=3}
                hits = rag_manager.vector_store.search(
                    q_emb, k=5
                )  # :contentReference[oaicite:4]{index=4}

                # Concatenate the top contexts and run rule/sanction extractors
                context_text = " ".join(h["text"] for h in hits)
                if not context_text.strip():
                    continue

                # numeric limits, country/entity lists (Phase 3 extractors):contentReference[oaicite:5]{index=5}
                extracted_rules.extend(
                    rag_manager.rule_extractor.extract_rules(context_text)
                )
                s_lists = rag_manager.rule_extractor.extract_sanctions_list(
                    context_text
                )
                sanctions["countries"].update(
                    map(str.strip, s_lists.get("countries", []))
                )
                sanctions["entities"].update(
                    map(str.strip, s_lists.get("entities", []))
                )

            # Pick highest-confidence/most recent numeric limits from extracted rules
            # Heuristic: prefer explicit types if multiple are present
            per_tx_limit = None
            daily_limit = None
            for r in extracted_rules:
                if r["rule_type"] == "transaction_limit" and isinstance(
                    r["rule_value"], (int, float)
                ):
                    per_tx_limit = (
                        float(r["rule_value"]) if per_tx_limit is None else per_tx_limit
                    )
                if r["rule_type"] == "transfer_limit" and isinstance(
                    r["rule_value"], (int, float)
                ):
                    daily_limit = (
                        float(r["rule_value"]) if daily_limit is None else daily_limit
                    )

            return per_tx_limit, daily_limit, sanctions

        (
            rag_per_tx_limit,
            rag_daily_limit,
            rag_sanctions,
        ) = await _rag_limits_and_sanctions()
    except Exception:
        # Be conservative but resilient if vector DB is empty or RAG errors out
        rag_per_tx_limit, rag_daily_limit, rag_sanctions = (
            None,
            None,
            {"countries": set(), "entities": set()},
        )

    # Effective limits: RAG overrides config if available:contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7}
    effective_per_tx = (
        float(rag_per_tx_limit)
        if rag_per_tx_limit
        else float(settings.per_transaction_limit)
    )
    effective_daily = (
        float(rag_daily_limit) if rag_daily_limit else float(user.daily_limit)
    )

    # 1) Per-transaction limit (RAG-aware)
    if amount > effective_per_tx:
        return (
            False,
            f"Amount exceeds per-transaction limit of {effective_per_tx:g} BHD",
        )

    # 2) Daily limit (RAG-aware)
    today = func.date(func.now())
    result = await db.execute(
        select(func.sum(Transaction.amount)).filter(
            Transaction.sender_id == user.id,
            func.date(Transaction.created_at) == today,
            Transaction.status == TransactionStatus.COMPLETED,
        )
    )
    daily_spent = result.scalar() or 0.0
    if daily_spent + amount > effective_daily:
        available = max(0.0, effective_daily - daily_spent)
        return False, f"Daily limit exceeded. Available today: {available:g} BHD"

    # 3) Sanctions checks
    # 3a) RAG-extracted lists (countries/entities)
    if rag_sanctions and rag_sanctions.get("countries"):
        # simple country name containment (normalize both sides)
        ben_country_norm = beneficiary.country.strip().lower()
        if any(
            ben_country_norm == c.strip().lower() for c in rag_sanctions["countries"]
        ):
            return (
                False,
                "Transfer blocked: Beneficiary country appears on a sanctioned/blacklisted list (RAG).",
            )

    # 3b) Mock API (second line of defense):contentReference[oaicite:8]{index=8}
    sanctions_check = await mock_banking_api.check_sanctions(
        beneficiary.name, beneficiary.country
    )
    if sanctions_check.data and sanctions_check.data.get("is_sanctioned"):
        return False, "Transfer blocked: Beneficiary is sanctioned"

    # All checks passed
    return True, None


@router.post("/transfer", response_model=TransactionResponse)
async def transfer_funds(
    transfer_request: TransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a fund transfer to a beneficiary"""
    # Get beneficiary
    result = await db.execute(
        select(Beneficiary).filter(
            Beneficiary.id == transfer_request.beneficiary_id,
            Beneficiary.user_id == current_user.id,
            Beneficiary.is_active == True,
        )
    )
    beneficiary = result.scalar_one_or_none()

    if not beneficiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficiary not found or inactive",
        )

    # Validate transfer
    is_valid, error_message = await validate_transfer(
        transfer_request.amount, current_user, beneficiary, db
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Create transaction
    transaction = Transaction(
        sender_id=current_user.id,
        beneficiary_id=beneficiary.id,
        amount=transfer_request.amount,
        currency=transfer_request.currency,
        type=TransactionType.TRANSFER,
        status=TransactionStatus.PENDING,
        description=transfer_request.description,
        reference_number=generate_reference_number(),
    )

    db.add(transaction)
    await db.commit()

    # Process transfer through mock API
    api_response = await mock_banking_api.process_transfer(
        str(current_user.id),
        beneficiary.iban,
        transfer_request.amount,
        transfer_request.currency,
    )

    if api_response.success:
        # Update transaction status
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()

        # Update user balance
        current_user.balance -= transfer_request.amount

        await db.commit()
    else:
        # Mark transaction as failed
        transaction.status = TransactionStatus.FAILED
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_response.message,
        )

    await db.refresh(transaction)
    return transaction


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
):
    """Get user's transaction history"""
    query = select(Transaction).filter(
        or_(
            Transaction.sender_id == current_user.id,
            Transaction.receiver_id == current_user.id,
        )
    )

    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)

    if status:
        query = query.filter(Transaction.status == status)

    query = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific transaction details"""
    result = await db.execute(
        select(Transaction).filter(
            Transaction.id == transaction_id,
            or_(
                Transaction.sender_id == current_user.id,
                Transaction.receiver_id == current_user.id,
            ),
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction
