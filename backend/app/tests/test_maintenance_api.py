def test_create_valid_ticket_returns_201(client, auth_headers):
    response = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "Kitchen sink is leaking"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "open"
    assert body["data"]["issue_type"] == "plumbing"


def test_create_ticket_with_missing_description_returns_validation_error(client, auth_headers):
    response = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_ticket_without_token_is_rejected(client):
    response = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "Kitchen sink is leaking"},
    )

    assert response.status_code == 401


def test_triage_escalates_water_leak(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "There is a water leak under the kitchen sink"},
        headers=auth_headers,
    ).json()["data"]

    triage = client.post(f"/api/v1/maintenance-tickets/{created['id']}/triage", headers=auth_headers)

    assert triage.status_code == 200
    result = triage.json()["data"]
    assert result["priority"] == "urgent"
    assert result["escalated"] is True
    assert result["vendor_queue"] == "plumbing-emergency"


def test_triage_normal_request_assigns_type_priority_and_queue(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "electrical", "description": "The living room outlet stopped working"},
        headers=auth_headers,
    ).json()["data"]

    triage = client.post(f"/api/v1/maintenance-tickets/{created['id']}/triage", headers=auth_headers)

    result = triage.json()["data"]
    assert result["issue_type"] == "electrical"
    assert result["priority"] == "medium"
    assert result["escalated"] is False
    assert result["vendor_queue"] == "electrical-standard"


def test_track_ticket_status_after_triage(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "hvac", "description": "AC is not cooling properly"},
        headers=auth_headers,
    ).json()["data"]

    client.post(f"/api/v1/maintenance-tickets/{created['id']}/triage", headers=auth_headers)

    tracked = client.get(f"/api/v1/maintenance-tickets/{created['id']}", headers=auth_headers)

    assert tracked.status_code == 200
    assert tracked.json()["data"]["status"] == "assigned"


def test_get_missing_ticket_returns_404(client, auth_headers):
    response = client.get(
        "/api/v1/maintenance-tickets/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


def test_resident_cannot_update_own_ticket(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "general", "description": "Squeaky door hinge"},
        headers=auth_headers,
    ).json()["data"]

    updated = client.patch(
        f"/api/v1/maintenance-tickets/{created['id']}",
        json={"status": "in_progress", "priority": "low"},
        headers=auth_headers,
    )

    assert updated.status_code == 403


def test_marking_resolved_sets_resolved_at_automatically(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "general", "description": "Loose cabinet handle"},
        headers=auth_headers,
    ).json()["data"]
    assert created["resolved_at"] is None

    resolved = client.patch(
        f"/api/v1/maintenance-tickets/{created['id']}",
        json={"status": "resolved"},
        headers=auth_headers,
    ).json()["data"]
    assert resolved["resolved_at"] is not None

    reopened = client.patch(
        f"/api/v1/maintenance-tickets/{created['id']}",
        json={"status": "open"},
        headers=auth_headers,
    ).json()["data"]
    assert reopened["resolved_at"] is None


def test_cancel_ticket_via_status_update(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "other", "description": "Resident changed their mind"},
        headers=auth_headers,
    ).json()["data"]

    cancelled = client.patch(
        f"/api/v1/maintenance-tickets/{created['id']}",
        json={"status": "cancelled"},
        headers=auth_headers,
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"


def test_create_ticket_with_photo_attachment(client, auth_headers):
    photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    response = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "Leaking pipe, photo attached", "photo_data_url": photo},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["data"]["photo_data_url"] == photo


def test_triage_reason_is_persisted_for_ticket_detail(client, auth_headers):
    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "There is a water leak under the kitchen sink"},
        headers=auth_headers,
    ).json()["data"]

    client.post(f"/api/v1/maintenance-tickets/{created['id']}/triage", headers=auth_headers)

    detail = client.get(f"/api/v1/maintenance-tickets/{created['id']}", headers=auth_headers)

    assert detail.status_code == 200
    assert detail.json()["data"]["triage_reason"] == "Water leak requires urgent escalation."


def test_resident_cannot_access_another_residents_ticket(client, auth_headers, db_session):
    import uuid as uuid_module

    from app.core.security import hash_password
    from app.models.guest import Guest
    from app.models.property import Property
    from app.models.resident_credential import ResidentCredential
    from app.models.unit import Unit

    other_guest = Guest(id=uuid_module.uuid4(), name="Other Resident", email=f"{uuid_module.uuid4()}@example.com")
    other_property = Property(id=uuid_module.uuid4(), name="Other Property", timezone="UTC")
    db_session.add_all([other_guest, other_property])
    db_session.flush()

    other_unit = Unit(id=uuid_module.uuid4(), property_id=other_property.id, unit_number="202", status="occupied")
    db_session.add(other_unit)
    db_session.flush()

    other_email = f"{uuid_module.uuid4()}@example.com"
    other_credential = ResidentCredential(
        id=uuid_module.uuid4(),
        guest_id=other_guest.id,
        unit_id=other_unit.id,
        email=other_email,
        password_hash=hash_password("OtherPass123!"),
        role="resident",
    )
    db_session.add(other_credential)
    db_session.commit()

    other_login = client.post("/api/v1/auth/login", json={"email": other_email, "password": "OtherPass123!"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    created = client.post(
        "/api/v1/maintenance-tickets",
        json={"issue_type": "plumbing", "description": "Leaking faucet"},
        headers=auth_headers,
    ).json()["data"]

    response = client.get(f"/api/v1/maintenance-tickets/{created['id']}", headers=other_headers)

    assert response.status_code == 403

