from typing import Optional

from fastapi import APIRouter, Query

from backend.models.schemas import MockApiResponse
from backend.utils.mock_apis import mock_banking_api

router = APIRouter()


@router.get("/balance/{account_id}", response_model=MockApiResponse)
async def check_balance(account_id: str):
    """Mock endpoint to check account balance"""
    return await mock_banking_api.check_balance(account_id)


@router.post("/validate-iban", response_model=MockApiResponse)
async def validate_iban(
    iban: str = Query(..., min_length=15, max_length=34),
    country: str = Query(..., min_length=2, max_length=50),
):
    """Mock endpoint to validate IBAN"""
    return await mock_banking_api.validate_iban(iban, country)


@router.post("/transfer", response_model=MockApiResponse)
async def process_transfer(
    from_account: str = Query(...),
    to_account: str = Query(...),
    amount: float = Query(..., gt=0),
    currency: str = Query(default="BHD"),
):
    """Mock endpoint to process fund transfer"""
    return await mock_banking_api.process_transfer(
        from_account, to_account, amount, currency
    )


@router.get("/sanctions-check", response_model=MockApiResponse)
async def check_sanctions(
    name: str = Query(..., min_length=2),
    country: str = Query(..., min_length=2),
):
    """Mock endpoint to check sanctions list"""
    return await mock_banking_api.check_sanctions(name, country)


@router.get("/verify-account", response_model=MockApiResponse)
async def verify_account(
    account_number: str = Query(..., min_length=8),
    bank_code: str = Query(..., min_length=4),
):
    """Mock endpoint to verify account"""
    return await mock_banking_api.verify_account(account_number, bank_code)
