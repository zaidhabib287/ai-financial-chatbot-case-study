#!/usr/bin/env python
"""Test script for Phase 2 functionality"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.skip("Phase 2 manual test script - skipped in automated tests")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000/api/v1"


async def test_auth_flow():
    """Test authentication flow"""
    async with httpx.AsyncClient() as client:
        print("\n=== Testing Authentication Flow ===")

        # Register a new user
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "role": "customer",
        }

        try:
            response = await client.post(
                f"{BASE_URL}/auth/register", json=register_data
            )
            if response.status_code == 200:
                print("✓ User registration successful")
                user = response.json()
                print(f"  User ID: {user['id']}")
            elif response.status_code == 400:
                print("! User already exists")
        except Exception as e:
            print(f"✗ Registration failed: {e}")

        # Login
        login_data = {"username": "testuser", "password": "TestPass123"}
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
        )

        if response.status_code == 200:
            print("✓ Login successful")
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"✗ Login failed: {response.text}")
            return None


async def test_user_endpoints(token: str):
    """Test user endpoints"""
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        print("\n=== Testing User Endpoints ===")

        # Get profile
        response = await client.get(f"{BASE_URL}/users/profile", headers=headers)
        if response.status_code == 200:
            print("✓ Get profile successful")
            profile = response.json()
            print(f"  Username: {profile['username']}")
            print(f"  Balance: {profile['balance']} BHD")

        # Get balance
        response = await client.get(f"{BASE_URL}/users/balance", headers=headers)
        if response.status_code == 200:
            print("✓ Get balance successful")
            balance_info = response.json()
            print(f"  Available today: {balance_info['available_today']} BHD")


async def test_mock_apis():
    """Test mock APIs"""
    async with httpx.AsyncClient() as client:
        print("\n=== Testing Mock APIs ===")

        # Test IBAN validation
        response = await client.post(
            f"{BASE_URL}/mock/validate-iban",
            params={"iban": "BH67BMAG00001299123456", "country": "Bahrain"},
        )
        if response.status_code == 200:
            print("✓ IBAN validation working")

        # Test sanctions check
        response = await client.get(
            f"{BASE_URL}/mock/sanctions-check",
            params={"name": "John Doe", "country": "USA"},
        )
        if response.status_code == 200:
            print("✓ Sanctions check working")


async def main():
    """Run all tests"""
    print("Testing Phase 2 Implementation...")

    # Test authentication
    token = await test_auth_flow()

    if token:
        # Test user endpoints
        await test_user_endpoints(token)

    # Test mock APIs
    await test_mock_apis()

    print("\n✓ Phase 2 tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
