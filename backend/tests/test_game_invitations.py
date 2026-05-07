"""
Tests for the game invitation rework — pending invitation model.

Covers:
- Dealer can invite an accepted friend → creates pending invitation
- Non-friend invitation blocked (403)
- Duplicate invitation blocked (409)
- Inviting a user already in the game blocked (409)
- Invited user accepts → becomes participant
- Invited user declines → invitation declined, not a participant
- Only invited user can accept/decline
- Accept on non-pending invitation blocked
- Old invite-user endpoint returns 410 Gone
- List pending invitations for game (dealer)
- List pending invitations for user
- Invite to closed game blocked
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


def _get_my_id(client: TestClient, token: str) -> str:
    r = client.get("/users/me", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _make_friends(client: TestClient, token_a: str, token_b: str) -> None:
    """Have user A send a request and user B accept it."""
    b_id = _get_my_id(client, token_b)
    req = client.post(
        "/friends/request",
        json={"addressee_user_id": b_id},
        headers=_auth(token_a),
    )
    assert req.status_code == 201, req.text
    fid = req.json()["id"]
    accept = client.post(f"/friends/{fid}/accept", headers=_auth(token_b))
    assert accept.status_code == 200, accept.text


def _create_game(client: TestClient, token: str) -> dict:
    resp = client.post(
        "/games",
        json={"title": "Poker Night", "chip_cash_rate": "0.01", "currency": "USD"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _invite_friend(client: TestClient, token: str, game_id: str, user_id: str) -> dict:
    resp = client.post(
        f"/games/{game_id}/invitations",
        json={"invited_user_id": user_id},
        headers=_auth(token),
    )
    return resp.json() if resp.status_code < 500 else {"status_code": resp.status_code}


# ---------------------------------------------------------------------------
# Tests — invitation creation
# ---------------------------------------------------------------------------


def test_dealer_invites_friend(client: TestClient) -> None:
    _register(client, "dealer@test.com", "Dealer")
    _register(client, "friend@test.com", "Friend")
    dt = _login(client, "dealer@test.com")
    ft = _login(client, "friend@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    resp = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "pending"
    assert data["invited_user_id"] == friend_id
    assert data["invited_user_display_name"] == "Friend"


def test_invite_non_friend_blocked(client: TestClient) -> None:
    _register(client, "dealer2@test.com", "Dealer")
    _register(client, "stranger@test.com", "Stranger")
    dt = _login(client, "dealer2@test.com")
    st = _login(client, "stranger@test.com")

    game = _create_game(client, dt)
    stranger_id = _get_my_id(client, st)

    resp = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": stranger_id},
        headers=_auth(dt),
    )
    assert resp.status_code == 403, resp.text
    assert "friends" in resp.json()["detail"].lower()


def test_duplicate_invitation_blocked(client: TestClient) -> None:
    _register(client, "dealer3@test.com", "Dealer")
    _register(client, "friend3@test.com", "Friend")
    dt = _login(client, "dealer3@test.com")
    ft = _login(client, "friend3@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    resp1 = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )
    assert resp2.status_code == 409


def test_invite_existing_participant_blocked(client: TestClient) -> None:
    _register(client, "dealer4@test.com", "Dealer")
    _register(client, "friend4@test.com", "Friend")
    dt = _login(client, "dealer4@test.com")
    ft = _login(client, "friend4@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    # Join via token first
    link_resp = client.post(f"/games/{game['id']}/invite-link", headers=_auth(dt))
    token = link_resp.json()["invite_token"]
    client.post("/games/join-by-token", json={"token": token}, headers=_auth(ft))

    resp = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )
    assert resp.status_code == 409
    assert "already a participant" in resp.json()["detail"].lower()


def test_invite_to_closed_game_blocked(client: TestClient) -> None:
    _register(client, "dealer5@test.com", "Dealer")
    _register(client, "friend5@test.com", "Friend")
    dt = _login(client, "dealer5@test.com")
    ft = _login(client, "friend5@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    game_id = game["id"]
    friend_id = _get_my_id(client, ft)

    # Start and close the game
    client.post(f"/games/{game_id}/start", headers=_auth(dt))

    # Get dealer participant id, add buy-in, set final stack, then close
    parts = client.get(f"/games/{game_id}/participants", headers=_auth(dt)).json()
    dealer_pid = parts[0]["id"]
    client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": dealer_pid, "cash_amount": "100", "chips_amount": "10000", "buy_in_type": "initial"},
        headers=_auth(dt),
    )
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": "10000"},
        headers=_auth(dt),
    )
    close_resp = client.post(f"/games/{game_id}/close", headers=_auth(dt))
    assert close_resp.status_code == 200, close_resp.text

    resp = client.post(
        f"/games/{game_id}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )
    assert resp.status_code == 400
    assert "closed" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests — accept/decline
# ---------------------------------------------------------------------------


def test_accept_invitation(client: TestClient) -> None:
    _register(client, "dealer6@test.com", "Dealer")
    _register(client, "friend6@test.com", "Friend")
    dt = _login(client, "dealer6@test.com")
    ft = _login(client, "friend6@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    inv = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    ).json()

    # Accept
    resp = client.post(
        f"/games/{game['id']}/invitations/{inv['id']}/accept",
        headers=_auth(ft),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "accepted"

    # Verify user is now a participant
    parts = client.get(f"/games/{game['id']}/participants", headers=_auth(ft)).json()
    participant_user_ids = [p["user_id"] for p in parts]
    assert friend_id in participant_user_ids


def test_decline_invitation(client: TestClient) -> None:
    _register(client, "dealer7@test.com", "Dealer")
    _register(client, "friend7@test.com", "Friend")
    dt = _login(client, "dealer7@test.com")
    ft = _login(client, "friend7@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    inv = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    ).json()

    # Decline
    resp = client.post(
        f"/games/{game['id']}/invitations/{inv['id']}/decline",
        headers=_auth(ft),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "declined"

    # Verify user is NOT a participant (only dealer should be there)
    parts = client.get(f"/games/{game['id']}/participants", headers=_auth(dt)).json()
    assert len(parts) == 1  # only dealer


def test_only_invited_user_can_accept(client: TestClient) -> None:
    _register(client, "dealer8@test.com", "Dealer")
    _register(client, "friend8@test.com", "Friend")
    _register(client, "other8@test.com", "Other")
    dt = _login(client, "dealer8@test.com")
    ft = _login(client, "friend8@test.com")
    ot = _login(client, "other8@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    inv = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    ).json()

    # Other user tries to accept
    resp = client.post(
        f"/games/{game['id']}/invitations/{inv['id']}/accept",
        headers=_auth(ot),
    )
    assert resp.status_code == 403


def test_accept_already_accepted_blocked(client: TestClient) -> None:
    _register(client, "dealer9@test.com", "Dealer")
    _register(client, "friend9@test.com", "Friend")
    dt = _login(client, "dealer9@test.com")
    ft = _login(client, "friend9@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    inv = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    ).json()

    # Accept first time
    client.post(
        f"/games/{game['id']}/invitations/{inv['id']}/accept",
        headers=_auth(ft),
    )
    # Accept again
    resp = client.post(
        f"/games/{game['id']}/invitations/{inv['id']}/accept",
        headers=_auth(ft),
    )
    assert resp.status_code == 400
    assert "not pending" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests — listing
# ---------------------------------------------------------------------------


def test_list_pending_for_game(client: TestClient) -> None:
    _register(client, "dealer10@test.com", "Dealer")
    _register(client, "friend10a@test.com", "FriendA")
    _register(client, "friend10b@test.com", "FriendB")
    dt = _login(client, "dealer10@test.com")
    fa = _login(client, "friend10a@test.com")
    fb = _login(client, "friend10b@test.com")
    _make_friends(client, dt, fa)
    _make_friends(client, dt, fb)

    game = _create_game(client, dt)
    a_id = _get_my_id(client, fa)
    b_id = _get_my_id(client, fb)

    client.post(f"/games/{game['id']}/invitations", json={"invited_user_id": a_id}, headers=_auth(dt))
    client.post(f"/games/{game['id']}/invitations", json={"invited_user_id": b_id}, headers=_auth(dt))

    resp = client.get(f"/games/{game['id']}/invitations", headers=_auth(dt))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_pending_for_user(client: TestClient) -> None:
    _register(client, "dealer11@test.com", "Dealer")
    _register(client, "friend11@test.com", "Friend")
    dt = _login(client, "dealer11@test.com")
    ft = _login(client, "friend11@test.com")
    _make_friends(client, dt, ft)

    friend_id = _get_my_id(client, ft)

    # Create two games and invite friend to both
    game1 = _create_game(client, dt)
    game2 = _create_game(client, dt)
    client.post(f"/games/{game1['id']}/invitations", json={"invited_user_id": friend_id}, headers=_auth(dt))
    client.post(f"/games/{game2['id']}/invitations", json={"invited_user_id": friend_id}, headers=_auth(dt))

    resp = client.get("/invitations/pending", headers=_auth(ft))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Tests — old endpoint deprecated
# ---------------------------------------------------------------------------


def test_old_invite_user_returns_410(client: TestClient) -> None:
    _register(client, "dealer12@test.com", "Dealer")
    dt = _login(client, "dealer12@test.com")
    game = _create_game(client, dt)

    resp = client.post(
        f"/games/{game['id']}/invite-user",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
        headers=_auth(dt),
    )
    assert resp.status_code == 410


# ---------------------------------------------------------------------------
# Tests — notification created on invitation
# ---------------------------------------------------------------------------


def test_invitation_creates_notification(client: TestClient) -> None:
    _register(client, "dealer13@test.com", "Dealer")
    _register(client, "friend13@test.com", "Friend")
    dt = _login(client, "dealer13@test.com")
    ft = _login(client, "friend13@test.com")
    _make_friends(client, dt, ft)

    game = _create_game(client, dt)
    friend_id = _get_my_id(client, ft)

    client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": friend_id},
        headers=_auth(dt),
    )

    # Check friend's notifications
    resp = client.get("/notifications", headers=_auth(ft))
    assert resp.status_code == 200
    notifications = resp.json()
    game_inv_notifs = [n for n in notifications if n["type"] == "game_invitation"]
    assert len(game_inv_notifs) >= 1
    latest = game_inv_notifs[0]
    assert latest["data"]["game_id"] == game["id"]
    assert "invitation_id" in latest["data"]


# ---------------------------------------------------------------------------
# Tests — non-dealer cannot invite
# ---------------------------------------------------------------------------


def test_non_dealer_cannot_invite(client: TestClient) -> None:
    _register(client, "dealer14@test.com", "Dealer")
    _register(client, "player14@test.com", "Player")
    _register(client, "target14@test.com", "Target")
    dt = _login(client, "dealer14@test.com")
    pt = _login(client, "player14@test.com")
    tt = _login(client, "target14@test.com")
    _make_friends(client, dt, pt)
    _make_friends(client, pt, tt)

    game = _create_game(client, dt)
    player_id = _get_my_id(client, pt)
    target_id = _get_my_id(client, tt)

    # Add player to game via invite+accept
    inv = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": player_id},
        headers=_auth(dt),
    ).json()
    client.post(f"/games/{game['id']}/invitations/{inv['id']}/accept", headers=_auth(pt))

    # Player (non-dealer) tries to invite target
    resp = client.post(
        f"/games/{game['id']}/invitations",
        json={"invited_user_id": target_id},
        headers=_auth(pt),
    )
    assert resp.status_code == 403
