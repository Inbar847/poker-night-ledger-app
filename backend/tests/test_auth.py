"""Tests for auth and user profile flows."""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_USER = {
    "email": "alice@example.com",
    "password": "password123",
    "full_name": "Alice Example",
}


def _register(client: TestClient, **overrides) -> dict:
    payload = {**_BASE_USER, **overrides}
    return client.post("/auth/register", json=payload)


def _login(client: TestClient, email: str = _BASE_USER["email"], password: str = _BASE_USER["password"]) -> dict:
    return client.post("/auth/login", json={"email": email, "password": password})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_success(client: TestClient):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice Example"
    assert "id" in body
    assert "created_at" in body
    assert "password_hash" not in body


def test_register_normalises_email_to_lowercase(client: TestClient):
    resp = _register(client, email="UPPER@Example.COM")
    assert resp.status_code == 201
    assert resp.json()["email"] == "upper@example.com"


def test_register_duplicate_email_returns_409(client: TestClient):
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_register_short_password_returns_422(client: TestClient):
    resp = _register(client, password="short")
    assert resp.status_code == 422


def test_register_invalid_email_returns_422(client: TestClient):
    resp = _register(client, email="not-an-email")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success_returns_tokens(client: TestClient):
    _register(client)
    resp = _login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client: TestClient):
    _register(client)
    resp = _login(client, password="wrongpassword")
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient):
    resp = _login(client, email="ghost@example.com")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


def test_refresh_issues_new_access_token(client: TestClient):
    _register(client)
    tokens = _login(client).json()
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["access_token"] != tokens["access_token"]


def test_refresh_with_access_token_returns_401(client: TestClient):
    _register(client)
    tokens = _login(client).json()
    # Passing an *access* token where a refresh token is expected
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_refresh_with_garbage_returns_401(client: TestClient):
    resp = client.post("/auth/refresh", json={"refresh_token": "not.a.jwt"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------


def test_get_me_returns_profile(client: TestClient):
    _register(client)
    token = _login(client).json()["access_token"]
    resp = client.get("/users/me", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


def test_get_me_without_token_returns_401(client: TestClient):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_with_garbage_token_returns_401(client: TestClient):
    resp = client.get("/users/me", headers=_auth_header("garbage.token.here"))
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /users/me
# ---------------------------------------------------------------------------


def test_update_profile_fields(client: TestClient):
    _register(client)
    token = _login(client).json()["access_token"]
    resp = client.patch(
        "/users/me",
        json={"full_name": "Alice Updated", "phone": "+1-555-0100"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Alice Updated"
    assert body["phone"] == "+1-555-0100"


def test_update_profile_partial_update(client: TestClient):
    _register(client)
    token = _login(client).json()["access_token"]
    # Only update phone — full_name should remain unchanged
    client.patch("/users/me", json={"full_name": "First Update"}, headers=_auth_header(token))
    resp = client.patch("/users/me", json={"phone": "+1-555-0200"}, headers=_auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "First Update"
    assert body["phone"] == "+1-555-0200"


def test_update_profile_image_url(client: TestClient):
    _register(client)
    token = _login(client).json()["access_token"]
    url = "https://example.com/avatar.jpg"
    resp = client.patch("/users/me", json={"profile_image_url": url}, headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["profile_image_url"] == url


def test_update_profile_without_token_returns_401(client: TestClient):
    resp = client.patch("/users/me", json={"full_name": "Ghost"})
    assert resp.status_code == 401
