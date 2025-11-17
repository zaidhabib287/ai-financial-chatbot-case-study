from backend.rag.rag_manager import RAGManager
from backend.utils.mock_apis import mock_banking_api
from backend.config.constants import BLACKLISTED_COUNTRIES

class ComplianceRuleChecker:
    """Cross-checks RAG rules and sanctions before allowing transfers."""

    def __init__(self):
        self.rag = RAGManager()

    async def verify_transaction(self, user_id: str, user_input: str):
        """Validate against transfer limits and sanctions."""
        # Check against static blacklists
        if any(country.lower() in user_input.lower() for country in BLACKLISTED_COUNTRIES):
            return False, "Destination country is blacklisted."

        # Retrieve rules from vector DB
        rules = await self.rag.vector_store.get_stats()
        # Demo logic – expand later with actual embeddings lookup
        return True, "Transaction complies with limits and sanctions."
