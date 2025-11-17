import io

import pytest


@pytest.mark.asyncio
async def test_upload_and_rag_stats(client):
    # admin
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin2",
            "email": "admin2@test.com",
            "password": "AdminPass1",
            "role": "admin",
        },
    )
    lr = await client.post(
        "/api/v1/auth/login", data={"username": "admin2", "password": "AdminPass1"}
    )
    h = {"Authorization": f"Bearer {lr.json()['access_token']}"}

    # upload rules doc
    content = io.BytesIO(
        b"Daily transfer limit is 1000 BHD. Per transaction limit is 500 BHD."
    )
    files = {"file": ("rules.txt", content, "text/plain")}
    data = {"document_type": "compliance_rules"}
    r = await client.post(
        "/api/v1/admin/documents/upload", headers=h, files=files, data=data
    )
    assert r.status_code == 200

    # (Background task will ingest; stats endpoint should respond regardless)
    s = await client.get("/api/v1/admin/rag/stats", headers=h)
    assert s.status_code == 200
    assert isinstance(s.json(), dict)
