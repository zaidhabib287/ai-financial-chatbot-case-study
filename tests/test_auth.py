import pytest


@pytest.mark.asyncio
async def test_register_login_admin(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin1",
            "email": "admin1@test.com",
            "password": "AdminPass1",
            "role": "admin",
        },
    )
    assert r.status_code == 200

    r = await client.post(
        "/api/v1/auth/login", data={"username": "admin1", "password": "AdminPass1"}
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
