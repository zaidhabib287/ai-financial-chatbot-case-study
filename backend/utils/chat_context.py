import asyncio
from typing import Dict

from sqlalchemy.future import select

from backend.models.database import get_db
from backend.models.models import Beneficiary, Transaction, User
from backend.utils.mock_apis import mock_banking_api


class ChatContextManager:
    """Interface between chatbot and backend logic."""

    async def fetch_balance(self, user_id: str) -> Dict[str, float]:
        async with get_db() as db:
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalar_one_or_none()
            return {"balance": user.balance if user else 0.0}

    async def add_beneficiary(self, user_id: str, user_input: str) -> Dict[str, str]:
        """Simplified addition flow (production version should parse structured input)."""
        await asyncio.sleep(0.2)
        return {"message": "Beneficiary added successfully (demo mode)."}

    async def execute_transfer(self, user_id: str, user_input: str) -> Dict[str, str]:
        """Mock transfer execution using API."""
        await asyncio.sleep(0.2)
        return {"message": "Transfer processed successfully (mock mode)."}
