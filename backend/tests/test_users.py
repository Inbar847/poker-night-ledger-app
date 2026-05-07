"""
Tests for user search, public profile, and friend-gated stats (Stage 12).
"""

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(client: TestClient, email: str, full_name: str = "Test User") -> dict:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "full_name": full_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client: TestClient, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _setup_two_users(client: TestClient):
    alice = _register(client, "alice@example.com", "Alice Smith")
    bob = _register(client, "bob@example.com", "Bob Jones")
    alice_token = _login(client, "alice@example.com")
    bob_token = _login(client, "bob@example.com")
    return alice_token, bob_token, alice["id"], bob["id"]


def _make_friends(client: TestClient, requester_token: str, addressee_id: str, addressee_token: str) -> str:
    """Send and accept a friend request; return friendship id."""
    req = client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(addressee_token))
    return req["id"]


# ---------------------------------------------------------------------------
# GET /users/search
# ---------------------------------------------------------------------------


def test_search_requires_auth(client: TestClient):
    resp = client.get("/users/search?q=alice")
    assert resp.status_code == 401


def test_search_by_name_finds_user(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    resp = client.get("/users/search?q=Bob", headers=_auth(alice_token))
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["id"] == bob_id
    assert results[0]["full_name"] == "Bob Jones"


def test_search_case_insensitive(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=bob", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_partial_name_match(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=Jon", headers=_auth(alice_token))
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Bob Jones"


def test_search_by_email_returns_no_results(client: TestClient):
    """Email is not a searchable field — an email-like query should match nothing."""
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=bob@", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_excludes_self(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    # Alice searching "Alice" should NOT see herself
    resp = client.get("/users/search?q=Alice", headers=_auth(alice_token))
    assert resp.status_code == 200
    for r in resp.json():
        assert r["full_name"] != "Alice Smith"


def test_search_no_sensitive_fields_in_results(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=Bob", headers=_auth(alice_token))
    assert resp.status_code == 200
    result = resp.json()[0]
    assert "email" not in result
    assert "password_hash" not in result
    assert "phone" not in result


def test_search_short_query_returns_empty(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    # Query shorter than 2 chars — returns empty without hitting DB
    resp = client.get("/users/search?q=B", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_empty_query_returns_empty(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_no_match_returns_empty(client: TestClient):
    alice_token, _, _, _ = _setup_two_users(client)

    resp = client.get("/users/search?q=Zorgon", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_returns_multiple_results(client: TestClient):
    _register(client, "charlie@example.com", "Charlie Smith")
    _register(client, "diana@example.com", "Diana Smith")
    alice_token = _login(client, "charlie@example.com")

    resp = client.get("/users/search?q=Smith", headers=_auth(alice_token))
    assert resp.status_code == 200
    # charlie (self) excluded; diana should appear
    names = {r["full_name"] for r in resp.json()}
    assert "Diana Smith" in names
    assert "Charlie Smith" not in names


# ---------------------------------------------------------------------------
# GET /users/{user_id}/profile
# ---------------------------------------------------------------------------


def test_get_public_profile_requires_auth(client: TestClient):
    _register(client, "alice@example.com", "Alice Smith")
    alice = _register(client, "bob@example.com", "Bob Jones")
    resp = client.get(f"/users/{alice['id']}/profile")
    assert resp.status_code == 401


def test_get_public_profile_success(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    resp = client.get(f"/users/{bob_id}/profile", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == bob_id
    assert body["full_name"] == "Bob Jones"
    assert "profile_image_url" in body


def test_get_public_profile_no_sensitive_fields(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    resp = client.get(f"/users/{bob_id}/profile", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "email" not in body
    assert "password_hash" not in body
    assert "phone" not in body


def test_get_public_profile_nonexistent_user_returns_404(client: TestClient):
    _register(client, "alice@example.com", "Alice Smith")
    alice_token = _login(client, "alice@example.com")

    resp = client.get(
        "/users/00000000-0000-0000-0000-000000000099/profile",
        headers=_auth(alice_token),
    )
    assert resp.status_code == 404


def test_get_own_public_profile(client: TestClient):
    alice = _register(client, "alice@example.com", "Alice Smith")
    alice_token = _login(client, "alice@example.com")

    resp = client.get(f"/users/{alice['id']}/profile", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Smith"


# ---------------------------------------------------------------------------
# GET /users/{user_id}/stats — privacy gating
# ---------------------------------------------------------------------------


def test_stats_requires_auth(client: TestClient):
    bob = _register(client, "bob@example.com", "Bob Jones")
    resp = client.get(f"/users/{bob['id']}/stats")
    assert resp.status_code == 401


def test_stats_nonexistent_user_returns_404(client: TestClient):
    _register(client, "alice@example.com", "Alice Smith")
    alice_token = _login(client, "alice@example.com")

    resp = client.get(
        "/users/00000000-0000-0000-0000-000000000099/stats",
        headers=_auth(alice_token),
    )
    assert resp.status_code == 404


def test_stats_self_returns_full_access(client: TestClient):
    alice = _register(client, "alice@example.com", "Alice Smith")
    alice_token = _login(client, "alice@example.com")

    resp = client.get(f"/users/{alice['id']}/stats", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_friend_access"] is True
    assert "total_games_played" in body
    assert "total_games_hosted" in body
    assert "win_rate" in body


def test_stats_non_friend_returns_restricted(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    resp = client.get(f"/users/{bob_id}/stats", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_friend_access"] is False
    assert "total_games_played" in body
    # Detailed fields should be null/absent
    assert body.get("total_games_hosted") is None
    assert body.get("cumulative_net") is None
    assert body.get("win_rate") is None
    assert body.get("recent_games") is None


def test_stats_friend_returns_full_access(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    _make_friends(client, alice_token, bob_id, bob_token)

    resp = client.get(f"/users/{bob_id}/stats", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_friend_access"] is True
    assert "total_games_hosted" in body
    assert "win_rate" in body
    assert "recent_games" in body


def test_stats_after_unfriend_returns_restricted(client: TestClient):
    """After removing a friendship, stats become restricted again."""
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    friendship_id = _make_friends(client, alice_token, bob_id, bob_token)

    # Confirm full access while friends
    resp = client.get(f"/users/{bob_id}/stats", headers=_auth(alice_token))
    assert resp.json()["is_friend_access"] is True

    # Unfriend
    client.delete(f"/friends/{friendship_id}", headers=_auth(alice_token))

    # Now restricted
    resp = client.get(f"/users/{bob_id}/stats", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json()["is_friend_access"] is False


def test_stats_friendship_is_bidirectional_for_access(client: TestClient):
    """Bob can also see Alice's full stats after Alice sent the request."""
    alice_token, bob_token, alice_id, bob_id = _setup_two_users(client)

    _make_friends(client, alice_token, bob_id, bob_token)

    # Bob looking at Alice's stats (Bob was the addressee)
    resp = client.get(f"/users/{alice_id}/stats", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["is_friend_access"] is True
