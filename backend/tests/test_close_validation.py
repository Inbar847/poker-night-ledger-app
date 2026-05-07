"""
Tests for close-game validation: missing final stacks.

Covers:
- Close blocked when any participant is missing a final stack (HTTP 400)
- Response includes missing_final_stacks array with participant_id and display_name
- Close succeeds when all participants have final stacks
- Close succeeds for a solo dealer game with final stack
- Close blocked when one of multiple participants is missing a final stack
"""

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, email: str, password: str = "pw12345678") -> tuple[str, str]:
    r = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    user_id = r.json()["id"]
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"], user_id


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_game(client: TestClient, token: str) -> dict:
    r = client.post(
        "/games",
        json={"title": "Validation Game", "chip_cash_rate": "0.01", "currency": "ILS"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _get_participants(client: TestClient, token: str, game_id: str) -> list[dict]:
    r = client.get(f"/games/{game_id}/participants", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _start(client: TestClient, token: str, game_id: str) -> None:
    r = client.post(f"/games/{game_id}/start", headers=_auth(token))
    assert r.status_code == 200, r.text


def _add_buy_in(client: TestClient, token: str, game_id: str, pid: str, cash: str, chips: str) -> None:
    r = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": pid, "cash_amount": cash, "chips_amount": chips, "buy_in_type": "initial"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text


def _set_final_stack(client: TestClient, token: str, game_id: str, pid: str, chips: str) -> None:
    r = client.put(
        f"/games/{game_id}/final-stacks/{pid}",
        json={"chips_amount": chips},
        headers=_auth(token),
    )
    assert r.status_code in (200, 201), r.text


def _close(client: TestClient, token: str, game_id: str) -> dict:
    return client.post(f"/games/{game_id}/close", json={}, headers=_auth(token))


def _invite_link(client: TestClient, token: str, game_id: str) -> str:
    r = client.post(f"/games/{game_id}/invite-link", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()["invite_token"]


def _join_by_token(client: TestClient, token: str, invite_token: str) -> dict:
    r = client.post(
        "/games/join-by-token",
        json={"token": invite_token},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _add_guest(client: TestClient, token: str, game_id: str, name: str) -> dict:
    r = client.post(
        f"/games/{game_id}/guests",
        json={"guest_name": name},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCloseGameValidation:
    def test_close_blocked_when_all_missing(self, client: TestClient):
        """Close is blocked when no participants have final stacks."""
        dealer_token, _ = _register_and_login(client, "cv_all_miss@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        parts = _get_participants(client, dealer_token, gid)
        pid = parts[0]["id"]
        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, pid, "100.00", "10000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 400
        body = r.json()
        assert body["detail"] == "Cannot close game: missing final chip counts"
        assert len(body["missing_final_stacks"]) == 1
        assert body["missing_final_stacks"][0]["participant_id"] == pid

    def test_close_succeeds_when_all_present(self, client: TestClient):
        """Close succeeds when all participants have final stacks."""
        dealer_token, _ = _register_and_login(client, "cv_all_ok@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        parts = _get_participants(client, dealer_token, gid)
        pid = parts[0]["id"]
        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, pid, "100.00", "10000")
        _set_final_stack(client, dealer_token, gid, pid, "10000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_close_blocked_when_one_of_many_missing(self, client: TestClient):
        """Close is blocked when one of multiple participants is missing a final stack."""
        dealer_token, _ = _register_and_login(client, "cv_partial_d@test.com")
        player_token, _ = _register_and_login(client, "cv_partial_p@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player_token, invite_tok)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        player_pid = next(p["id"] for p in parts if p["role_in_game"] == "player")

        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "10000")
        _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "10000")

        # Only set final stack for dealer, not player
        _set_final_stack(client, dealer_token, gid, dealer_pid, "10000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 400
        body = r.json()
        assert len(body["missing_final_stacks"]) == 1
        assert body["missing_final_stacks"][0]["participant_id"] == player_pid
        # Verify display_name is included
        assert body["missing_final_stacks"][0]["display_name"] != ""

    def test_close_blocked_guest_missing_final_stack(self, client: TestClient):
        """Close is blocked when a guest participant is missing a final stack."""
        dealer_token, _ = _register_and_login(client, "cv_guest_miss@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]

        guest = _add_guest(client, dealer_token, gid, "Guest Alice")
        guest_pid = guest["id"]

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")

        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "10000")
        _add_buy_in(client, dealer_token, gid, guest_pid, "50.00", "5000")

        # Set final stack for dealer only
        _set_final_stack(client, dealer_token, gid, dealer_pid, "10000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 400
        body = r.json()
        missing_names = [m["display_name"] for m in body["missing_final_stacks"]]
        assert "Guest Alice" in missing_names

    def test_missing_response_lists_multiple_participants(self, client: TestClient):
        """When multiple participants are missing, all are listed."""
        dealer_token, _ = _register_and_login(client, "cv_multi_d@test.com")
        player_token, _ = _register_and_login(client, "cv_multi_p@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player_token, invite_tok)
        _add_guest(client, dealer_token, gid, "Guest Bob")

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        for p in parts:
            _add_buy_in(client, dealer_token, gid, p["id"], "50.00", "5000")

        # No final stacks set at all
        r = _close(client, dealer_token, gid)
        assert r.status_code == 400
        body = r.json()
        assert len(body["missing_final_stacks"]) == 3
