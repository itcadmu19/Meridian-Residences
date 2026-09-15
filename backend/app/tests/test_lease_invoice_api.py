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


def test_resident_submits_payment_for_staff_approval(client):
    headers = seeded_headers(client)
    generated = client.post(
        "/api/v1/invoices/generate",
        json={
            "lease_id": "77777777-7777-7777-7777-777777777777",
            "billing_period_start": "2027-01-17",
            "billing_period_end": "2027-01-31",
            "due_date": "2027-02-20",
        },
        headers=headers,
    )
    invoice_id = generated.json()["data"]["id"]
    response = client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["payment_status"] == "payment_submitted"
    assert response.json()["data"]["billing_period_start"] == "2027-01-01"
    assert response.json()["data"]["billing_period_end"] == "2027-01-10"
    assert response.json()["data"]["due_date"] == "2027-01-11"
    assert response.json()["data"]["paid_at"] is None


def test_resident_cannot_approve_own_payment(client):
    headers = seeded_headers(client)
    response = client.patch(
        "/api/v1/invoices/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/payment-status",
        json={"payment_status": "paid"},
        headers=headers,
    )

    assert response.status_code == 403


def test_staff_can_approve_submitted_payment(client):
    resident_headers = seeded_headers(client)
    generated = client.post(
        "/api/v1/invoices/generate",
        json={
            "lease_id": "77777777-7777-7777-7777-777777777777",
            "billing_period_start": "2027-02-17",
            "billing_period_end": "2027-02-28",
            "due_date": "2027-03-20",
        },
        headers=resident_headers,
    )
    invoice_id = generated.json()["data"]["id"]
    submitted = client.post(
        f"/api/v1/invoices/{invoice_id}/pay",
        headers=resident_headers,
    )
    assert submitted.status_code == 200

    staff_login = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@meridian.com", "password": "StaffPass123!"},
    )
    assert staff_login.status_code == 200
    staff_headers = {"Authorization": f"Bearer {staff_login.json()['access_token']}"}
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/payment-status",
        json={"payment_status": "paid"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["payment_status"] == "paid"
    assert response.json()["data"]["paid_at"] is not None


def test_staff_can_extend_due_date_and_period_end_moves_with_it(client):
    resident_headers = seeded_headers(client)
    generated = client.post(
        "/api/v1/invoices/generate",
        json={
            "lease_id": "77777777-7777-7777-7777-777777777777",
            "billing_period_start": "2027-03-17",
            "billing_period_end": "2027-03-31",
            "due_date": "2027-04-20",
        },
        headers=resident_headers,
    )
    invoice_id = generated.json()["data"]["id"]
    staff_login = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@meridian.com", "password": "StaffPass123!"},
    )
    staff_headers = {"Authorization": f"Bearer {staff_login.json()['access_token']}"}
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/due-date",
        json={"due_date": "2027-04-25"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["due_date"] == "2027-04-25"
    assert response.json()["data"]["billing_period_end"] == "2027-04-24"
    assert response.json()["data"]["payment_status"] == "due_extended"

    resident_invoice = client.get(f"/api/v1/invoices/{invoice_id}", headers=resident_headers)
    assert resident_invoice.status_code == 200
    assert resident_invoice.json()["data"]["payment_status"] == "due_extended"

    payment = client.post(f"/api/v1/invoices/{invoice_id}/pay", headers=resident_headers)
    assert payment.status_code == 200
    assert payment.json()["data"]["payment_status"] == "payment_submitted"


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


def test_pending_invoice_past_due_date_is_auto_flagged_overdue(client):
    headers = seeded_headers(client)
    payload = {
        "lease_id": "77777777-7777-7777-7777-777777777777",
        "billing_period_start": "2026-01-01",
        "billing_period_end": "2026-01-31",
        "due_date": "2026-02-10",
    }
    generated = client.post("/api/v1/invoices/generate", json=payload, headers=headers)
    assert generated.status_code == 201
    assert generated.json()["data"]["payment_status"] == "pending"

    listed = client.get("/api/v1/invoices?page=1&page_size=50", headers=headers)
    assert listed.status_code == 200
    invoice = next(inv for inv in listed.json()["data"] if inv["id"] == generated.json()["data"]["id"])
    assert invoice["payment_status"] == "overdue"


def test_invoice_list_filters_by_date_range(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/invoices?date_from=2026-08-01&date_to=2026-08-31", headers=headers
    )
    assert response.status_code == 200
    for invoice in response.json()["data"]:
        assert "2026-08" in invoice["due_date"]


def test_resident_cannot_mark_overdue(client):
    headers = seeded_headers(client)
    response = client.post("/api/v1/invoices/mark-overdue", headers=headers)
    assert response.status_code == 403


def test_invoice_insights_returns_risk_summary(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/invoices/insights?lease_id=77777777-7777-7777-7777-777777777777", headers=headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_level"] in ("low", "medium", "high")
    assert data["total_invoices_considered"] >= 3
    assert isinstance(data["insight"], str) and len(data["insight"]) > 0


def test_download_single_invoice_pdf(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/invoices/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/pdf", headers=headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_download_filtered_invoice_statement_pdf(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/invoices/export/pdf?payment_status=paid", headers=headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_cannot_download_pdf_for_other_residents_invoice(client):
    headers = seeded_headers(client)
    response = client.get(
        "/api/v1/invoices/00000000-0000-0000-0000-000000000000/pdf", headers=headers
    )
    assert response.status_code == 404
