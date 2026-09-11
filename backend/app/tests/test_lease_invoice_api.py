from datetime import date


def seeded_headers(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "anu.sharma@example.com", "password": "ResidentPass123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_resident_can_view_own_lease(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/leases/77777777-7777-7777-7777-777777777777", headers=headers
    )

    assert response.status_code == 200
    lease = response.json()["data"]
    assert lease["status"] == "active"
    assert lease["unit_number"] == "101"
    assert float(lease["monthly_rate"]) == 45000.0


def test_resident_can_view_lease_summary(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/leases/77777777-7777-7777-7777-777777777777/summary", headers=headers
    )

    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["lease"]["id"] == "77777777-7777-7777-7777-777777777777"
    assert summary["open_maintenance_count"] >= 0


def test_resident_can_list_own_leases(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/guests/11111111-1111-1111-1111-111111111111/leases", headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


def test_resident_can_list_invoices(client):
    headers = seeded_headers(client)
    response = client.get("/api/v1/invoices?page=1&page_size=20", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 3
    assert {invoice["payment_status"] for invoice in body["data"]} >= {"paid", "overdue"}


def test_invoice_generation_is_idempotent(client):
    headers = seeded_headers(client)
    payload = {
        "lease_id": "77777777-7777-7777-7777-777777777777",
        "billing_period_start": "2026-09-01",
        "billing_period_end": "2026-09-30",
        "due_date": "2026-10-10",
    }

    first = client.post("/api/v1/invoices/generate", json=payload, headers=headers)
    second = client.post("/api/v1/invoices/generate", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert second.json()["message"] == "Existing invoice returned"


def test_resident_can_update_own_invoice_payment_status(client):
    headers = seeded_headers(client)
    response = client.patch(
        "/api/v1/invoices/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/payment-status",
        json={"payment_status": "paid"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["payment_status"] == "paid"
    assert response.json()["data"]["paid_at"] is not None


def test_resident_cannot_generate_batch(client):
    headers = seeded_headers(client)
    response = client.post(
        "/api/v1/invoices/generate-batch",
        json={
            "billing_period_start": "2026-10-01",
            "billing_period_end": "2026-10-31",
            "due_date": "2026-11-10",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_missing_lease_returns_404(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/leases/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
