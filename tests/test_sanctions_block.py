import io, pytest

@pytest.mark.asyncio
async def test_transfer_blocked_by_sanctions(client):
    # admin + customer
    await client.post("/api/v1/auth/register", json={
        "username":"admin4","email":"a4@test.com","password":"AdminPass1","role":"admin"
    })
    ad = await client.post("/api/v1/auth/login", data={"username":"admin4","password":"AdminPass1"})
    hadmin = {"Authorization": f"Bearer {ad.json()['access_token']}"}

    await client.post("/api/v1/auth/register", json={
        "username":"cust2","email":"c2@test.com","password":"CustPass1","role":"customer"
    })
    cd = await client.post("/api/v1/auth/login", data={"username":"cust2","password":"CustPass1"})
    hcust = {"Authorization": f"Bearer {cd.json()['access_token']}"}

    # Upload sanctions doc
    content = io.BytesIO(b"Sanctioned countries: North Korea, Iran, Syria")
    files = {"file": ("sanctions.txt", content, "text/plain")}
    data = {"document_type": "sanctions_list"}
    await client.post("/api/v1/admin/documents/upload", headers=hadmin, files=files, data=data)

    # credit
    users = await client.get("/api/v1/admin/users", headers=hadmin)
    cust_id = [u["id"] for u in users.json() if u["username"]=="cust2"][0]
    await client.post(f"/api/v1/admin/users/{cust_id}/credit", headers=hadmin,
                      json={"user_id": cust_id, "amount": 600, "operation_type": "credit"})

    # beneficiary in blacklisted country
    b = await client.post("/api/v1/beneficiaries/", headers=hcust, json={
        "name":"John Doe","bank_name":"Some Bank",
        "iban":"IR062960000000100324200001", "country":"Iran"  # blacklisted by RAG
    })
    ben = b.json()

    t = await client.post("/api/v1/transactions/transfer", headers=hcust, json={
        "beneficiary_id": ben["id"], "amount": 100, "currency":"BHD", "description":"sanction test"
    })
    assert t.status_code == 400
    assert "blocked" in t.json()["detail"].lower()
