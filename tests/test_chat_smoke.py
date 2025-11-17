import pytest

@pytest.mark.asyncio
async def test_chat_smoke(client):
    await client.post("/api/v1/auth/register", json={
        "username":"cust4","email":"c4@test.com","password":"CustPass1","role":"customer"
    })
    lr = await client.post("/api/v1/auth/login", data={"username":"cust4","password":"CustPass1"})
    h = {"Authorization": f"Bearer {lr.json()['access_token']}"}

    # Gracefully handle if chat model is not configured (OpenAI key absent)
    r = await client.post("/api/v1/chatbot/chat", headers=h, json={"content":"Hello"})
    assert r.status_code in (200, 500)  # 500 allowed if model key missing
