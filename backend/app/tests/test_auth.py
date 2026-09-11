def test_login_with_valid_credentials_returns_token(client, resident_credential):
    _, email, password = resident_credential
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["role"] == "resident"


def test_login_with_wrong_password_returns_401(client, resident_credential):
    _, email, _ = resident_credential
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})

    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(client):
    response = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"})

    assert response.status_code == 401
