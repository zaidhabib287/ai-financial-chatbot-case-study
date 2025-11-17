import io, pytest

@pytest.mark.asyncio
async def test_transfer_happy_path(client):
    # admin and customer
    await client.post("/api/v1/auth/register", json={
        "username":"admin3","email":"a3@test.com","password":"AdminPass1","role":"admin"
    })
    ad = await client.post("/api/v1/auth/login", data={"username":"admin3","password":"AdminPass1"})
    hadmin = {"Authorization": f"Bearer {ad.json()['access_token']}"}

    await client.post("/api/v1/auth/register", json={
        "username":"cust1","email":"c1@test.com","password":"CustPass1","role":"customer"
    })
    cd = await client.post("/api/v1/auth/login", data={"username":"cust1","password":"CustPass1"})
    hcust = {"Authorization": f"Bearer {cd.json()['access_token']}"}

    # Upload + ingest rules (background)
    content = io.BytesIO(b"Daily transfer limit is 1000 BHD. Per transaction limit is 500 BHD.")
    files = {"file": ("rules.txt", content, "text/plain")}
    data = {"document_type": "compliance_rules"}
    await client.post("/api/v1/admin/documents/upload", headers=hadmin, files=files, data=data)

    # Admin list users to get cust1 id
    users = await client.get("/api/v1/admin/users", headers=hadmin)
    cust_id = [u["id"] for u in users.json() if u["username"]=="cust1"][0]

    # Credit 600
    r = await client.post(f"/api/v1/admin/users/{cust_id}/credit", headers=hadmin,
                          json={"user_id": cust_id, "amount": 600, "operation_type": "credit"})
    assert r.status_code == 200

    # Add beneficiary
    b = await client.post("/api/v1/beneficiaries/", headers=hcust, json={
        "name":"Ahmed","bank_name":"Kuwait Bank",
        "iban":"KW81CBKU0000000000001234560101","country":"Kuwait"
    })
    assert b.status_code in (200, 201)
    ben = b.json()

    # Transfer within per-tx limit (200 <= 500)
    t = await client.post("/api/v1/transactions/transfer", headers=hcust, json={
        "beneficiary_id": ben["id"], "amount": 200, "currency": "BHD", "description": "test"
    })
    assert t.status_code == 200
    assert t.json()["status"].lower() == "completed"
