#!/usr/bin/env python
"""Test script to verify basic setup"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_imports():
    """Test that all modules can be imported"""
    try:
        from backend.config.settings import settings

        print("✓ Settings loaded successfully")
        print(f"  App: {settings.app_name} v{settings.app_version}")

        from backend.config.logger import logger  # noqa: F401

        print("✓ Logger configured successfully")

        from backend.models.database import engine  # noqa: F401

        print("✓ Database engine created successfully")

        from backend.models.models import Transaction, User  # noqa: F401

        print("✓ Models imported successfully")

        from backend.main import app  # noqa: F401

        print("✓ FastAPI app created successfully")

        print("\nAll imports successful! Setup is complete.")

    except Exception as e:
        print(f"✗ Error during import: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_imports())
