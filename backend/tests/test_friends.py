"""Tests for the friends system: request lifecycle, permission guards, edge cases,
and notification side-effects added in Stage 13."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType

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
    """Register Alice and Bob and return (alice_token, bob_token, alice_id, bob_id)."""
    alice = _register(client, "alice@example.com", "Alice")
    bob = _register(client, "bob@example.com", "Bob")
    alice_token = _login(client, "alice@example.com")
    bob_token = _login(client, "bob@example.com")
    return alice_token, bob_token, alice["id"], bob["id"]


# ---------------------------------------------------------------------------
# POST /friends/request
# ---------------------------------------------------------------------------


def test_send_friend_request_success(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["addressee_user_id"] == bob_id


def test_send_friend_request_requires_auth(client: TestClient):
    _, _, _, bob_id = _setup_two_users(client)
    resp = client.post("/friends/request", json={"addressee_user_id": bob_id})
    assert resp.status_code == 401


def test_send_friend_request_to_self_returns_400(client: TestClient):
    alice = _register(client, "alice@example.com", "Alice")
    alice_token = _login(client, "alice@example.com")

    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": alice["id"]},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 400


def test_send_friend_request_to_unknown_user_returns_404(client: TestClient):
    _register(client, "alice@example.com", "Alice")
    alice_token = _login(client, "alice@example.com")

    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": "00000000-0000-0000-0000-000000000099"},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 404


def test_send_duplicate_request_returns_409(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 409


def test_reverse_request_while_pending_returns_409(client: TestClient):
    """Bob cannot send a request to Alice if Alice already sent one to Bob."""
    alice_token, bob_token, alice_id, bob_id = _setup_two_users(client)

    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": alice_id},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 409


def test_request_when_already_friends_returns_409(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /friends/{id}/accept
# ---------------------------------------------------------------------------


def test_accept_request_success(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()

    resp = client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_accept_by_requester_returns_403(client: TestClient):
    """Alice (requester) cannot accept her own request."""
    alice_token, _, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()

    resp = client.post(f"/friends/{req['id']}/accept", headers=_auth(alice_token))
    assert resp.status_code == 403


def test_accept_already_accepted_returns_400(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))
    resp = client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))
    assert resp.status_code == 400


def test_accept_nonexistent_friendship_returns_404(client: TestClient):
    _register(client, "alice@example.com", "Alice")
    alice_token = _login(client, "alice@example.com")
    resp = client.post(
        "/friends/00000000-0000-0000-0000-000000000001/accept",
        headers=_auth(alice_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /friends/{id}/decline
# ---------------------------------------------------------------------------


def test_decline_request_success(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()

    resp = client.post(f"/friends/{req['id']}/decline", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"


def test_decline_by_requester_returns_403(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()

    resp = client.post(f"/friends/{req['id']}/decline", headers=_auth(alice_token))
    assert resp.status_code == 403


def test_decline_already_declined_returns_400(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/decline", headers=_auth(bob_token))
    resp = client.post(f"/friends/{req['id']}/decline", headers=_auth(bob_token))
    assert resp.status_code == 400


def test_declined_request_blocks_re_request(client: TestClient):
    """A declined row blocks the same pair from creating a new request."""
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/decline", headers=_auth(bob_token))

    resp = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /friends/{id}
# ---------------------------------------------------------------------------


def test_remove_friend_by_requester(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.delete(f"/friends/{req['id']}", headers=_auth(alice_token))
    assert resp.status_code == 204


def test_remove_friend_by_addressee(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.delete(f"/friends/{req['id']}", headers=_auth(bob_token))
    assert resp.status_code == 204


def test_remove_pending_friendship_returns_400(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()

    resp = client.delete(f"/friends/{req['id']}", headers=_auth(alice_token))
    assert resp.status_code == 400


def test_remove_friend_third_party_returns_403(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)
    charlie = _register(client, "charlie@example.com", "Charlie")
    charlie_token = _login(client, "charlie@example.com")

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.delete(f"/friends/{req['id']}", headers=_auth(charlie_token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /friends
# ---------------------------------------------------------------------------


def test_list_friends_empty(client: TestClient):
    _register(client, "alice@example.com", "Alice")
    alice_token = _login(client, "alice@example.com")
    resp = client.get("/friends", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_friends_after_accept(client: TestClient):
    alice_token, bob_token, alice_id, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    # Both users should see each other in their friends list
    alice_friends = client.get("/friends", headers=_auth(alice_token)).json()
    bob_friends = client.get("/friends", headers=_auth(bob_token)).json()

    assert len(alice_friends) == 1
    assert alice_friends[0]["friend"]["id"] == bob_id

    assert len(bob_friends) == 1
    assert bob_friends[0]["friend"]["id"] == alice_id


def test_list_friends_excludes_pending(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )

    resp = client.get("/friends", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_friends_after_remove_is_empty(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))
    client.delete(f"/friends/{req['id']}", headers=_auth(alice_token))

    resp = client.get("/friends", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /friends/requests/incoming & outgoing
# ---------------------------------------------------------------------------


def test_incoming_requests(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )

    resp = client.get("/friends/requests/incoming", headers=_auth(bob_token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "pending"


def test_outgoing_requests(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)

    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )

    resp = client.get("/friends/requests/outgoing", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "pending"


def test_incoming_requests_empty_after_accept(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.get("/friends/requests/incoming", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# are_friends service function (tested indirectly via friends list)
# ---------------------------------------------------------------------------


def test_are_friends_bidirectional(client: TestClient):
    """Verified via friends list: both directions see the friend after accept."""
    alice_token, bob_token, alice_id, bob_id = _setup_two_users(client)

    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    alice_friends = client.get("/friends", headers=_auth(alice_token)).json()
    bob_friends = client.get("/friends", headers=_auth(bob_token)).json()

    assert any(f["friend"]["id"] == bob_id for f in alice_friends)
    assert any(f["friend"]["id"] == alice_id for f in bob_friends)


def test_unauthenticated_access_returns_401(client: TestClient):
    resp = client.get("/friends")
    assert resp.status_code == 401

    resp = client.get("/friends/requests/incoming")
    assert resp.status_code == 401

    resp = client.get("/friends/requests/outgoing")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /friends/status/{user_id}
# ---------------------------------------------------------------------------


def test_friendship_status_not_friends(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)
    resp = client.get(f"/friends/status/{bob_id}", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_friends"
    assert body["friendship_id"] is None


def test_friendship_status_pending_outgoing(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)
    client.post("/friends/request", json={"addressee_user_id": bob_id}, headers=_auth(alice_token))

    resp = client.get(f"/friends/status/{bob_id}", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_outgoing"


def test_friendship_status_pending_incoming(client: TestClient):
    alice_token, bob_token, alice_id, bob_id = _setup_two_users(client)
    client.post("/friends/request", json={"addressee_user_id": bob_id}, headers=_auth(alice_token))

    # From Bob's perspective, it looks like an incoming request from Alice
    resp = client.get(f"/friends/status/{alice_id}", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_incoming"


def test_friendship_status_friends(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)
    req = client.post(
        "/friends/request", json={"addressee_user_id": bob_id}, headers=_auth(alice_token)
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    resp = client.get(f"/friends/status/{bob_id}", headers=_auth(alice_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "friends"


def test_friendship_status_self_returns_400(client: TestClient):
    alice = _register(client, "alice@example.com", "Alice")
    alice_token = _login(client, "alice@example.com")
    resp = client.get(f"/friends/status/{alice['id']}", headers=_auth(alice_token))
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Notification side-effects (Stage 13)
# ---------------------------------------------------------------------------


def test_send_request_creates_notification_for_addressee(client: TestClient, db_session: Session):
    """Sending a friend request must create a friend_request_received notification."""
    alice_token, _, _, bob_id_str = _setup_two_users(client)
    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id_str},
        headers=_auth(alice_token),
    )

    bob_uuid = uuid.UUID(bob_id_str)
    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == bob_uuid,
            Notification.type == NotificationType.friend_request_received,
        )
        .all()
    )
    assert len(notifications) == 1
    assert notifications[0].read is False
    assert notifications[0].data is not None


def test_accept_request_creates_notification_for_requester(client: TestClient, db_session: Session):
    """Accepting a friend request must create a friend_request_accepted notification."""
    alice_token, bob_token, alice_id_str, bob_id_str = _setup_two_users(client)
    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id_str},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/accept", headers=_auth(bob_token))

    alice_uuid = uuid.UUID(alice_id_str)
    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == alice_uuid,
            Notification.type == NotificationType.friend_request_accepted,
        )
        .all()
    )
    assert len(notifications) == 1
    assert notifications[0].read is False


def test_decline_request_does_not_create_notification(client: TestClient, db_session: Session):
    """Declining a request must NOT create any notification (spec: requester is not informed)."""
    alice_token, bob_token, alice_id_str, bob_id_str = _setup_two_users(client)
    req = client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id_str},
        headers=_auth(alice_token),
    ).json()
    client.post(f"/friends/{req['id']}/decline", headers=_auth(bob_token))

    alice_uuid = uuid.UUID(alice_id_str)
    accepted_notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == alice_uuid,
            Notification.type == NotificationType.friend_request_accepted,
        )
        .all()
    )
    assert len(accepted_notifications) == 0


# ---------------------------------------------------------------------------
# Enriched incoming/outgoing request shape (Stage 13 router change)
# ---------------------------------------------------------------------------


def test_incoming_requests_enriched_with_requester_info(client: TestClient):
    alice_token, bob_token, _, bob_id = _setup_two_users(client)
    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )

    resp = client.get("/friends/requests/incoming", headers=_auth(bob_token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert "requester" in body[0]
    assert body[0]["requester"]["full_name"] == "Alice"


def test_outgoing_requests_enriched_with_addressee_info(client: TestClient):
    alice_token, _, _, bob_id = _setup_two_users(client)
    client.post(
        "/friends/request",
        json={"addressee_user_id": bob_id},
        headers=_auth(alice_token),
    )

    resp = client.get("/friends/requests/outgoing", headers=_auth(alice_token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert "addressee" in body[0]
    assert body[0]["addressee"]["full_name"] == "Bob"
