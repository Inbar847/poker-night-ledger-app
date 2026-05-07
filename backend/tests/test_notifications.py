"""
Tests for the notifications API and notification side-effects.

Covers:
- GET /notifications (list, newest-first, auth-scoped)
- GET /notifications/unread-count
- POST /notifications/{id}/read (mark single as read)
- POST /notifications/read-all (mark all as read)
- game_started notifications for registered participants (not guests)
- game_closed notifications for registered participants (not guests)
"""

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers (duplicated from test_games.py to keep test files independent)
# ---------------------------------------------------------------------------

_GAME_PAYLOAD = {
    "title": "Notification Test Game",
    "chip_cash_rate": 0.01,
    "currency": "USD",
}


def _register_and_login(client: TestClient, email: str, password: str = "pw123456") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_and_start_game(client: TestClient, dealer_token: str) -> dict:
    """Create a game, start it, and return the game dict."""
    game = client.post("/games", json=_GAME_PAYLOAD, headers=_auth(dealer_token)).json()
    client.post(f"/games/{game['id']}/start", headers=_auth(dealer_token))
    return game


def _create_game(client: TestClient, dealer_token: str) -> dict:
    return client.post("/games", json=_GAME_PAYLOAD, headers=_auth(dealer_token)).json()


# ---------------------------------------------------------------------------
# List / empty state
# ---------------------------------------------------------------------------


def test_list_notifications_empty(client: TestClient):
    token = _register_and_login(client, "user@example.com")
    resp = client.get("/notifications", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_notifications_requires_auth(client: TestClient):
    resp = client.get("/notifications")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Unread count
# ---------------------------------------------------------------------------


def test_unread_count_zero(client: TestClient):
    token = _register_and_login(client, "user@example.com")
    resp = client.get("/notifications/unread-count", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_unread_count_increments_with_friend_request(client: TestClient):
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    resp = client.get("/notifications/unread-count", headers=_auth(addressee_token))
    assert resp.json()["count"] == 1


def test_unread_count_is_scoped_to_user(client: TestClient):
    """A notification for user A does not appear in user B's count."""
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    bystander_token = _register_and_login(client, "bystander@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    assert client.get("/notifications/unread-count", headers=_auth(bystander_token)).json()["count"] == 0


# ---------------------------------------------------------------------------
# Notifications list — friend request side-effects
# ---------------------------------------------------------------------------


def test_friend_request_creates_notification_for_addressee(client: TestClient):
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    notifications = client.get("/notifications", headers=_auth(addressee_token)).json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "friend_request_received"
    assert notifications[0]["read"] is False


def test_accept_request_creates_notification_for_requester(client: TestClient):
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    friendship = client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    ).json()

    client.post(
        f"/friends/{friendship['id']}/accept",
        headers=_auth(addressee_token),
    )

    requester_notifications = client.get("/notifications", headers=_auth(requester_token)).json()
    types = [n["type"] for n in requester_notifications]
    assert "friend_request_accepted" in types


def test_notifications_ordered_newest_first(client: TestClient):
    """Two notifications created in sequence — newest should be first."""
    requester1_token = _register_and_login(client, "req1@example.com")
    requester2_token = _register_and_login(client, "req2@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester1_token),
    )
    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester2_token),
    )

    notifications = client.get("/notifications", headers=_auth(addressee_token)).json()
    assert len(notifications) == 2
    # Newest-first: second request's notification should appear before first
    assert notifications[0]["created_at"] >= notifications[1]["created_at"]


# ---------------------------------------------------------------------------
# Mark single notification as read
# ---------------------------------------------------------------------------


def test_mark_notification_read(client: TestClient):
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    notification_id = client.get("/notifications", headers=_auth(addressee_token)).json()[0]["id"]

    resp = client.post(f"/notifications/{notification_id}/read", headers=_auth(addressee_token))
    assert resp.status_code == 200
    assert resp.json()["read"] is True

    count = client.get("/notifications/unread-count", headers=_auth(addressee_token)).json()["count"]
    assert count == 0


def test_mark_notification_read_idempotent(client: TestClient):
    """Marking an already-read notification returns 200 without error."""
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    notification_id = client.get("/notifications", headers=_auth(addressee_token)).json()[0]["id"]
    client.post(f"/notifications/{notification_id}/read", headers=_auth(addressee_token))
    resp = client.post(f"/notifications/{notification_id}/read", headers=_auth(addressee_token))
    assert resp.status_code == 200
    assert resp.json()["read"] is True


def test_cannot_mark_other_users_notification(client: TestClient):
    requester_token = _register_and_login(client, "requester@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    attacker_token = _register_and_login(client, "attacker@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester_token),
    )

    notification_id = client.get("/notifications", headers=_auth(addressee_token)).json()[0]["id"]

    resp = client.post(f"/notifications/{notification_id}/read", headers=_auth(attacker_token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Mark all as read
# ---------------------------------------------------------------------------


def test_mark_all_read(client: TestClient):
    requester1_token = _register_and_login(client, "req1@example.com")
    requester2_token = _register_and_login(client, "req2@example.com")
    addressee_token = _register_and_login(client, "addressee@example.com")
    addressee_id = client.get("/users/me", headers=_auth(addressee_token)).json()["id"]

    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester1_token),
    )
    client.post(
        "/friends/request",
        json={"addressee_user_id": addressee_id},
        headers=_auth(requester2_token),
    )

    resp = client.post("/notifications/read-all", headers=_auth(addressee_token))
    assert resp.status_code == 200
    assert resp.json()["marked_read"] == 2

    count = client.get("/notifications/unread-count", headers=_auth(addressee_token)).json()["count"]
    assert count == 0


def test_mark_all_read_returns_zero_when_none_unread(client: TestClient):
    token = _register_and_login(client, "user@example.com")
    resp = client.post("/notifications/read-all", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["marked_read"] == 0


# ---------------------------------------------------------------------------
# Delete all notifications
# ---------------------------------------------------------------------------


def test_delete_all_notifications(client: TestClient):
    """DELETE /notifications permanently removes all notification rows."""
    token_a = _register_and_login(client, "userA@example.com")
    token_b = _register_and_login(client, "userB@example.com")

    me_b = client.get("/users/me", headers=_auth(token_b)).json()

    # A sends friend request to B → B gets a friend_request_received notification.
    client.post(
        "/friends/request",
        json={"addressee_user_id": me_b["id"]},
        headers=_auth(token_a),
    )

    notifs_b = client.get("/notifications", headers=_auth(token_b)).json()
    assert len(notifs_b) >= 1

    # Delete all for B
    resp = client.delete("/notifications", headers=_auth(token_b))
    assert resp.status_code == 204

    # B sees empty list now
    notifs_b = client.get("/notifications", headers=_auth(token_b)).json()
    assert notifs_b == []

    # Unread count is 0
    count = client.get("/notifications/unread-count", headers=_auth(token_b)).json()["count"]
    assert count == 0


def test_delete_all_notifications_is_no_op_when_empty(client: TestClient):
    """DELETE /notifications on empty list returns 204."""
    token = _register_and_login(client, "empty@example.com")
    resp = client.delete("/notifications", headers=_auth(token))
    assert resp.status_code == 204


def test_delete_all_notifications_does_not_affect_other_users(client: TestClient):
    """Deleting all notifications for one user does not affect another."""
    token_a = _register_and_login(client, "keepA@example.com")
    token_b = _register_and_login(client, "keepB@example.com")

    me_b = client.get("/users/me", headers=_auth(token_b)).json()

    # A sends friend request to B → B gets notification
    friendship = client.post(
        "/friends/request",
        json={"addressee_user_id": me_b["id"]},
        headers=_auth(token_a),
    ).json()

    # B accepts → A gets friend_request_accepted notification
    client.post(f"/friends/{friendship['id']}/accept", headers=_auth(token_b))

    notifs_a = client.get("/notifications", headers=_auth(token_a)).json()
    assert len(notifs_a) >= 1

    # Delete B's notifications
    client.delete("/notifications", headers=_auth(token_b))

    # A's notifications are untouched
    notifs_a_after = client.get("/notifications", headers=_auth(token_a)).json()
    assert len(notifs_a_after) == len(notifs_a)


def test_delete_all_requires_auth(client: TestClient):
    resp = client.delete("/notifications")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# game_started notifications
# ---------------------------------------------------------------------------


def test_game_started_notifies_registered_participants(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token)
    player_id = client.get("/users/me", headers=_auth(player_token)).json()["id"]

    # Player joins via invite token
    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )

    # Dealer starts the game
    resp = client.post(f"/games/{game['id']}/start", headers=_auth(dealer_token))
    assert resp.status_code == 200

    # Both dealer and player should receive game_started notifications
    dealer_notifications = client.get("/notifications", headers=_auth(dealer_token)).json()
    player_notifications = client.get("/notifications", headers=_auth(player_token)).json()

    dealer_types = [n["type"] for n in dealer_notifications]
    player_types = [n["type"] for n in player_notifications]

    assert "game_started" in dealer_types
    assert "game_started" in player_types


def test_game_started_does_not_notify_guests(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, dealer_token)

    # Add a guest (no user account)
    client.post(
        f"/games/{game['id']}/guests",
        json={"guest_name": "Guest Bob"},
        headers=_auth(dealer_token),
    )

    # Start the game — dealer gets notification; Guest Bob (no user) must not
    client.post(f"/games/{game['id']}/start", headers=_auth(dealer_token))

    # Dealer gets exactly one game_started notification (for themselves)
    dealer_notifications = client.get("/notifications", headers=_auth(dealer_token)).json()
    game_started = [n for n in dealer_notifications if n["type"] == "game_started"]
    assert len(game_started) == 1
    # The total count is 1 (dealer only), not 2 — guest was skipped
    assert dealer_notifications[0]["data"]["game_id"] == game["id"]


# ---------------------------------------------------------------------------
# game_closed notifications
# ---------------------------------------------------------------------------


def test_game_closed_notifies_registered_participants(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")
    game = _create_game(client, dealer_token)

    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )
    client.post(f"/games/{game['id']}/start", headers=_auth(dealer_token))
    parts = client.get(f"/games/{game['id']}/participants", headers=_auth(dealer_token)).json()
    for p in parts:
        client.put(f"/games/{game['id']}/final-stacks/{p['id']}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    resp = client.post(f"/games/{game['id']}/close", headers=_auth(dealer_token))
    assert resp.status_code == 200

    dealer_notifications = client.get("/notifications", headers=_auth(dealer_token)).json()
    player_notifications = client.get("/notifications", headers=_auth(player_token)).json()

    dealer_types = [n["type"] for n in dealer_notifications]
    player_types = [n["type"] for n in player_notifications]

    assert "game_closed" in dealer_types
    assert "game_closed" in player_types
