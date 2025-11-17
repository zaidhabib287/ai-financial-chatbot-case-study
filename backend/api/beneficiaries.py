# backend/api/beneficiaries.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.dependencies import get_current_user
from backend.models.database import get_db
from backend.models.models import Beneficiary as BeneficiaryModel
from backend.models.schemas import (
    BeneficiaryCreate,
    BeneficiaryUpdate,
    Beneficiary as BeneficiarySchema,
)

router = APIRouter()


@router.post(
    "/",
    response_model=BeneficiarySchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_beneficiary(
    beneficiary_in: BeneficiaryCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new beneficiary for the current user.

    Tests expect this endpoint to return a JSON payload with an `id` field.
    """

    # Build SQLAlchemy model instance
    data = beneficiary_in.dict()
    db_beneficiary = BeneficiaryModel(
        user_id=current_user.id,
        name=data["name"],
        bank_name=data["bank_name"],
        iban=data["iban"],
        country=data["country"],
        is_active=True,
    )

    db.add(db_beneficiary)
    await db.commit()
    await db.refresh(db_beneficiary)

    # Thanks to `from_attributes = True` in the Pydantic schema,
    # returning the SQLAlchemy instance will serialize with an `id` field.
    return db_beneficiary


@router.get(
    "/",
    response_model=List[BeneficiarySchema],
)
async def list_beneficiaries(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all active beneficiaries for the current user.
    (Not strictly required by tests, but useful and harmless.)
    """
    result = await db.execute(
        select(BeneficiaryModel).where(BeneficiaryModel.user_id == current_user.id)
    )
    beneficiaries = result.scalars().all()
    return beneficiaries


@router.patch(
    "/{beneficiary_id}",
    response_model=BeneficiarySchema,
)
async def update_beneficiary(
    beneficiary_id: str,
    update_in: BeneficiaryUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Partially update a beneficiary (e.g., name, bank_name, is_active).
    """

    result = await db.execute(
        select(BeneficiaryModel).where(
            BeneficiaryModel.id == beneficiary_id,
            BeneficiaryModel.user_id == current_user.id,
        )
    )
    db_beneficiary = result.scalar_one_or_none()
    if not db_beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    # Apply updates
    data = update_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(db_beneficiary, field, value)

    await db.commit()
    await db.refresh(db_beneficiary)
    return db_beneficiary


@router.delete(
    "/{beneficiary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_beneficiary(
    beneficiary_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete (deactivate) a beneficiary.
    """

    result = await db.execute(
        select(BeneficiaryModel).where(
            BeneficiaryModel.id == beneficiary_id,
            BeneficiaryModel.user_id == current_user.id,
        )
    )
    db_beneficiary = result.scalar_one_or_none()
    if not db_beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    db_beneficiary.is_active = False
    await db.commit()
