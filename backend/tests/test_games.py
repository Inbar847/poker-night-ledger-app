"""Tests for game creation, joining, and participant management."""

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GAME_PAYLOAD = {
    "title": "Friday Night Poker",
    "chip_cash_rate": 0.01,
    "currency": "USD",
}


def _register_and_login(client: TestClient, email: str, password: str = "password123") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_game(client: TestClient, token: str, **overrides) -> dict:
    payload = {**_GAME_PAYLOAD, **overrides}
    return client.post("/games", json=payload, headers=_auth(token))


# ---------------------------------------------------------------------------
# Create game
# ---------------------------------------------------------------------------


def test_create_game_success(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Friday Night Poker"
    assert body["status"] == "lobby"
    assert body["currency"] == "USD"
    assert body["invite_token"] is not None
    assert body["closed_at"] is None


def test_create_game_sets_dealer_fields(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token)
    body = resp.json()
    # dealer_user_id and created_by_user_id are the same user for MVP
    assert body["dealer_user_id"] == body["created_by_user_id"]


def test_create_game_requires_auth(client: TestClient):
    resp = client.post("/games", json=_GAME_PAYLOAD)
    assert resp.status_code == 401


def test_create_game_invalid_chip_rate(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token, chip_cash_rate=0)
    assert resp.status_code == 422


def test_create_game_empty_title(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token, title="")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List games
# ---------------------------------------------------------------------------


def test_list_games_returns_own_games(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    _create_game(client, token)
    _create_game(client, token, title="Second Game")
    resp = client.get("/games", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_games_does_not_return_others_games(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    other_token = _register_and_login(client, "other@example.com")
    _create_game(client, dealer_token)
    resp = client.get("/games", headers=_auth(other_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_games_requires_auth(client: TestClient):
    resp = client.get("/games")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get game
# ---------------------------------------------------------------------------


def test_get_game_success(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, token).json()["id"]
    resp = client.get(f"/games/{game_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == game_id


def test_get_game_forbidden_for_non_participant(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    other_token = _register_and_login(client, "other@example.com")
    game_id = _create_game(client, dealer_token).json()["id"]
    resp = client.get(f"/games/{game_id}", headers=_auth(other_token))
    assert resp.status_code == 403


def test_get_game_not_found(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(f"/games/{fake_id}", headers=_auth(token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Create game → dealer participant is created automatically
# ---------------------------------------------------------------------------


def test_create_game_dealer_appears_in_participants(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, token).json()["id"]
    resp = client.get(f"/games/{game_id}/participants", headers=_auth(token))
    assert resp.status_code == 200
    participants = resp.json()
    assert len(participants) == 1
    assert participants[0]["role_in_game"] == "dealer"
    assert participants[0]["participant_type"] == "registered"


# ---------------------------------------------------------------------------
# Invite link (rotate)
# ---------------------------------------------------------------------------


def test_generate_invite_link_returns_token(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, token).json()
    original_token = game["invite_token"]
    resp = client.post(f"/games/{game['id']}/invite-link", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "invite_token" in body
    # Rotating generates a new token
    assert body["invite_token"] != original_token


def test_generate_invite_link_dealer_only(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token).json()
    # Join as player first
    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    resp = client.post(f"/games/{game['id']}/invite-link", headers=_auth(player_token))
    assert resp.status_code == 403


def test_generate_invite_link_requires_auth(client: TestClient):
    token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, token).json()["id"]
    resp = client.post(f"/games/{game_id}/invite-link")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Join by token
# ---------------------------------------------------------------------------


def test_join_by_token_success(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token).json()

    resp = client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["role_in_game"] == "player"
    assert body["participant_type"] == "registered"
    assert body["game_id"] == game["id"]


def test_join_by_token_invalid_token(client: TestClient):
    player_token = _register_and_login(client, "player@example.com")
    resp = client.post(
        "/games/join-by-token",
        json={"token": "does-not-exist"},
        headers=_auth(player_token),
    )
    assert resp.status_code == 404


def test_join_by_token_already_participant_returns_409(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token).json()

    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    resp = client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    assert resp.status_code == 409


def test_join_by_token_requires_auth(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, dealer_token).json()
    resp = client.post("/games/join-by-token", json={"token": game["invite_token"]})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Invite registered user (deprecated — old endpoint returns 410 Gone)
# The full invitation flow is now tested in test_game_invitations.py.
# ---------------------------------------------------------------------------


def test_invite_user_deprecated_returns_410(client: TestClient):
    """The old POST /games/{id}/invite-user endpoint is deprecated."""
    dealer_token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, dealer_token).json()["id"]

    resp = client.post(
        f"/games/{game_id}/invite-user",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 410
    assert "deprecated" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Add guest
# ---------------------------------------------------------------------------


def test_add_guest_success(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, dealer_token).json()["id"]
    resp = client.post(
        f"/games/{game_id}/guests",
        json={"guest_name": "Bob Guest"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["guest_name"] == "Bob Guest"
    assert body["participant_type"] == "guest"
    assert body["user_id"] is None


def test_add_multiple_guests_allowed(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, dealer_token).json()["id"]
    client.post(f"/games/{game_id}/guests", json={"guest_name": "Guest 1"}, headers=_auth(dealer_token))
    resp = client.post(f"/games/{game_id}/guests", json={"guest_name": "Guest 2"}, headers=_auth(dealer_token))
    assert resp.status_code == 201


def test_add_guest_dealer_only(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token).json()
    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    resp = client.post(
        f"/games/{game['id']}/guests",
        json={"guest_name": "Sneaky Guest"},
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Get participants
# ---------------------------------------------------------------------------


def test_get_participants_includes_all_types(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token).json()

    # Add a registered player
    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    # Add a guest
    client.post(
        f"/games/{game['id']}/guests",
        json={"guest_name": "Alice Guest"},
        headers=_auth(dealer_token),
    )

    resp = client.get(f"/games/{game['id']}/participants", headers=_auth(dealer_token))
    assert resp.status_code == 200
    participants = resp.json()
    assert len(participants) == 3  # dealer + registered player + guest
    types = {p["participant_type"] for p in participants}
    assert "registered" in types
    assert "guest" in types


def test_get_participants_forbidden_for_non_participant(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    outsider_token = _register_and_login(client, "outsider@example.com")
    game_id = _create_game(client, dealer_token).json()["id"]
    resp = client.get(f"/games/{game_id}/participants", headers=_auth(outsider_token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Stage 9: validation edge cases
# ---------------------------------------------------------------------------


def test_create_game_whitespace_only_title_returns_422(client: TestClient):
    """Game title consisting only of whitespace must be rejected."""
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token, title="   ")
    assert resp.status_code == 422


def test_create_game_title_is_stripped(client: TestClient):
    """Leading/trailing whitespace in title should be stripped on the way in."""
    token = _register_and_login(client, "dealer@example.com")
    resp = _create_game(client, token, title="  Friday Night  ")
    assert resp.status_code == 201
    assert resp.json()["title"] == "Friday Night"


def test_add_guest_whitespace_only_name_returns_422(client: TestClient):
    """Guest name consisting only of whitespace must be rejected."""
    token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, token).json()["id"]
    resp = client.post(
        f"/games/{game_id}/guests",
        json={"guest_name": "   "},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_add_guest_name_is_stripped(client: TestClient):
    """Leading/trailing whitespace in guest_name should be stripped."""
    token = _register_and_login(client, "dealer@example.com")
    game_id = _create_game(client, token).json()["id"]
    resp = client.post(
        f"/games/{game_id}/guests",
        json={"guest_name": "  Bob  "},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert resp.json()["guest_name"] == "Bob"
