import asyncio
import random
import string
from datetime import datetime
from typing import Optional

from backend.config.settings import settings
from backend.models.schemas import MockApiResponse


def generate_reference_number(prefix: str = "TXN") -> str:
    """Generate a unique reference number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_suffix}"


async def mock_delay():
    """Simulate API processing delay"""
    if settings.mock_api_delay > 0:
        await asyncio.sleep(settings.mock_api_delay)


async def mock_failure() -> bool:
    """Randomly fail based on configured rate"""
    return random.random() < settings.mock_api_failure_rate


class MockBankingAPI:
    """Mock banking API for testing"""

    @staticmethod
    async def check_balance(account_id: str) -> MockApiResponse:
        """Mock balance check API"""
        await mock_delay()

        if await mock_failure():
            return MockApiResponse(
                success=False,
                message="Service temporarily unavailable",
                data=None,
            )

        # Generate random balance for testing
        balance = round(random.uniform(100, 10000), 2)

        return MockApiResponse(
            success=True,
            message="Balance retrieved successfully",
            data={
                "account_id": account_id,
                "balance": balance,
                "currency": "BHD",
                "available_balance": balance * 0.95,  # 95% available
            },
        )

    @staticmethod
    async def validate_iban(iban: str, country: str) -> MockApiResponse:
        """Mock IBAN validation API"""
        await mock_delay()

        # Basic IBAN validation (simplified)
        if len(iban) < 15 or len(iban) > 34:
            return MockApiResponse(
                success=False,
                message="Invalid IBAN format",
                data={"iban": iban, "valid": False},
            )

        return MockApiResponse(
            success=True,
            message="IBAN validated successfully",
            data={
                "iban": iban,
                "country": country,
                "valid": True,
                "bank_code": iban[4:8],
                "account_number": iban[8:],
            },
        )

    @staticmethod
    async def process_transfer(
        from_account: str,
        to_account: str,
        amount: float,
        currency: str = "BHD",
    ) -> MockApiResponse:
        """Mock fund transfer API"""
        await mock_delay()

        if await mock_failure():
            return MockApiResponse(
                success=False,
                message="Transfer processing failed. Please try again.",
                data=None,
            )

        reference = generate_reference_number()

        return MockApiResponse(
            success=True,
            message="Transfer processed successfully",
            data={
                "reference_number": reference,
                "from_account": from_account,
                "to_account": to_account,
                "amount": amount,
                "currency": currency,
                "fee": round(amount * 0.001, 2),  # 0.1% fee
                "total_amount": round(amount * 1.001, 2),
                "processing_time": "instant",
                "estimated_arrival": "within 24 hours",
            },
        )

    @staticmethod
    async def check_sanctions(name: str, country: str) -> MockApiResponse:
        """Mock sanctions list check API"""
        await mock_delay()

        # Simulate sanctions check
        sanctioned_countries = ["North Korea", "Iran", "Syria"]
        sanctioned_names = ["test_sanctioned_person", "blocked_entity"]

        is_sanctioned = (
            country in sanctioned_countries or name.lower() in sanctioned_names
        )

        return MockApiResponse(
            success=True,
            message="Sanctions check completed",
            data={
                "name": name,
                "country": country,
                "is_sanctioned": is_sanctioned,
                "risk_level": "high" if is_sanctioned else "low",
                "checked_lists": ["UN", "EU", "US_OFAC"],
            },
        )

    @staticmethod
    async def verify_account(account_number: str, bank_code: str) -> MockApiResponse:
        """Mock account verification API"""
        await mock_delay()

        if len(account_number) < 8:
            return MockApiResponse(
                success=False,
                message="Invalid account number",
                data=None,
            )

        return MockApiResponse(
            success=True,
            message="Account verified successfully",
            data={
                "account_number": account_number,
                "bank_code": bank_code,
                "account_holder": f"John Doe {account_number[-4:]}",
                "account_type": "Savings",
                "is_active": True,
            },
        )


# Create instance for easy import
mock_banking_api = MockBankingAPI()
