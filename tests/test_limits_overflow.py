import io, pytest

@pytest.mark.asyncio
async def test_per_transaction_limit_exceeded(client):
    # admin + customer
    await client.post("/api/v1/auth/register", json={
        "username":"admin5","email":"a5@test.com","password":"AdminPass1","role":"admin"
    })
    ad = await client.post("/api/v1/auth/login", data={"username":"admin5","password":"AdminPass1"})
    hadmin = {"Authorization": f"Bearer {ad.json()['access_token']}"}

    await client.post("/api/v1/auth/register", json={
        "username":"cust3","email":"c3@test.com","password":"CustPass1","role":"customer"
    })
    cd = await client.post("/api/v1/auth/login", data={"username":"cust3","password":"CustPass1"})
    hcust = {"Authorization": f"Bearer {cd.json()['access_token']}"}

    # Upload rule with per-tx 500
    content = io.BytesIO(b"Per transaction limit is 500 BHD.")
    files = {"file": ("rules.txt", content, "text/plain")}
    data = {"document_type": "compliance_rules"}
    await client.post("/api/v1/admin/documents/upload", headers=hadmin, files=files, data=data)

    # credit 2k
    users = await client.get("/api/v1/admin/users", headers=hadmin)
    cust_id = [u["id"] for u in users.json() if u["username"]=="cust3"][0]
    await client.post(f"/api/v1/admin/users/{cust_id}/credit", headers=hadmin,
                      json={"user_id": cust_id, "amount": 2000, "operation_type": "credit"})

    # beneficiary
    b = await client.post("/api/v1/beneficiaries/", headers=hcust, json={
        "name":"Sara","bank_name":"Bank A",
        "iban":"BH67BMAG00001299123456", "country":"Bahrain"
    })
    ben = b.json()

    # try transfer 700 (> 500)
    t = await client.post("/api/v1/transactions/transfer", headers=hcust, json={
        "beneficiary_id": ben["id"], "amount": 700, "currency":"BHD", "description":"limit test"
    })
    assert t.status_code == 400
    assert "per-transaction" in t.json()["detail"].lower()
