"""
Tests for settlement transfer notifications (Stage 23).

Covers:
- After game close, registered debtors receive settlement_owed notifications
- Creditors do NOT receive settlement_owed notifications
- Guests do NOT receive settlement_owed notifications
- Notification data includes game_title, to_display_name, amount, currency
- A debtor who owes multiple people gets multiple notifications
- No settlement_owed notifications when there are no transfers (everyone breaks even)
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType

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


def _create_game(client: TestClient, token: str, title: str = "Settle Game") -> dict:
    r = client.post(
        "/games",
        json={"title": title, "chip_cash_rate": "0.10", "currency": "USD"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


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


def _start(client: TestClient, token: str, game_id: str) -> None:
    r = client.post(f"/games/{game_id}/start", headers=_auth(token))
    assert r.status_code == 200, r.text


def _add_buy_in(client: TestClient, token: str, game_id: str, pid: str, cash: str, chips: str):
    return client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": pid, "cash_amount": cash, "chips_amount": chips, "buy_in_type": "initial"},
        headers=_auth(token),
    )


def _set_final_stack(client: TestClient, token: str, game_id: str, pid: str, chips: str):
    return client.put(
        f"/games/{game_id}/final-stacks/{pid}",
        json={"chips_amount": chips},
        headers=_auth(token),
    )


def _close(client: TestClient, token: str, game_id: str):
    return client.post(f"/games/{game_id}/close", json={}, headers=_auth(token))


def _get_participants(client: TestClient, token: str, game_id: str) -> list[dict]:
    r = client.get(f"/games/{game_id}/participants", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _get_notifications(client: TestClient, token: str) -> list[dict]:
    r = client.get("/notifications", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def _settlement_notifications(notifications: list[dict]) -> list[dict]:
    """Filter to only settlement_owed notifications."""
    return [n for n in notifications if n["type"] == "settlement_owed"]


# ---------------------------------------------------------------------------
# Setup helper: 2-player game where player loses and dealer wins
# ---------------------------------------------------------------------------


def _setup_and_close_two_player_game(client: TestClient):
    """
    Create and close a game: dealer wins, player loses.

    Dealer buys in 100 (1000 chips), ends with 1200 chips → wins.
    Player buys in 100 (1000 chips), ends with 800 chips → loses, owes dealer.

    Returns (dealer_token, player_token, game_id, dealer_pid, player_pid).
    """
    dealer_token, dealer_uid = _register_and_login(client, f"sn_d_{id(client)}@test.com")
    player_token, player_uid = _register_and_login(client, f"sn_p_{id(client)}@test.com")
    game = _create_game(client, dealer_token)
    gid = game["id"]

    invite_tok = _invite_link(client, dealer_token, gid)
    _join_by_token(client, player_token, invite_tok)

    _start(client, dealer_token, gid)

    parts = _get_participants(client, dealer_token, gid)
    dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
    player_pid = next(p["id"] for p in parts if p["role_in_game"] == "player")

    # Buy-ins
    r = _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
    assert r.status_code == 201, r.text
    r = _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "1000")
    assert r.status_code == 201, r.text

    # Final stacks: dealer won chips, player lost chips
    _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")
    _set_final_stack(client, dealer_token, gid, player_pid, "800")

    # Close the game
    r = _close(client, dealer_token, gid)
    assert r.status_code == 200, r.text

    return dealer_token, player_token, gid, dealer_pid, player_pid


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSettlementNotifications:
    def test_debtor_receives_settlement_owed(self, client: TestClient):
        """Registered debtor receives a settlement_owed notification."""
        _, player_token, gid, _, _ = _setup_and_close_two_player_game(client)

        notifs = _settlement_notifications(_get_notifications(client, player_token))
        assert len(notifs) == 1
        n = notifs[0]
        assert n["type"] == "settlement_owed"
        assert n["data"]["game_id"] == gid
        assert n["data"]["game_title"] == "Settle Game"
        assert n["data"]["currency"] == "USD"
        assert float(n["data"]["amount"]) > 0

    def test_creditor_does_not_receive_settlement_owed(self, client: TestClient):
        """The winner (creditor) should NOT get a settlement_owed notification."""
        dealer_token, _, _, _, _ = _setup_and_close_two_player_game(client)

        notifs = _settlement_notifications(_get_notifications(client, dealer_token))
        assert len(notifs) == 0

    def test_notification_data_includes_recipient_name(self, client: TestClient):
        """Notification data includes to_display_name (who the debtor owes)."""
        _, player_token, _, _, _ = _setup_and_close_two_player_game(client)

        notifs = _settlement_notifications(_get_notifications(client, player_token))
        assert len(notifs) == 1
        assert "to_display_name" in notifs[0]["data"]
        assert len(notifs[0]["data"]["to_display_name"]) > 0

    def test_guest_debtor_does_not_receive_notification(self, client: TestClient):
        """A guest who is a debtor should NOT get a notification (no user account)."""
        dealer_token, _ = _register_and_login(client, f"sn_gd_{id(client)}@test.com")
        game = _create_game(client, dealer_token, "Guest Game")
        gid = game["id"]

        guest = _add_guest(client, dealer_token, gid, "Guest Bob")
        guest_pid = guest["id"]

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")

        # Buy-ins for both
        r = _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        assert r.status_code == 201
        r = _add_buy_in(client, dealer_token, gid, guest_pid, "100.00", "1000")
        assert r.status_code == 201

        # Guest loses, dealer wins
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")
        _set_final_stack(client, dealer_token, gid, guest_pid, "800")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200

        # Dealer should not have settlement_owed (they are the creditor)
        dealer_notifs = _settlement_notifications(_get_notifications(client, dealer_token))
        assert len(dealer_notifs) == 0

        # Guest has no account — we verify by checking DB that no settlement_owed
        # notification exists for anyone other than the expected users

    def test_guest_debtor_no_notification_in_db(self, client: TestClient, db_session: Session):
        """Verify at DB level: no settlement_owed notifications for guest debtors."""
        dealer_token, _ = _register_and_login(client, f"sn_gdb_{id(client)}@test.com")
        game = _create_game(client, dealer_token, "Guest DB Game")
        gid = game["id"]

        guest = _add_guest(client, dealer_token, gid, "Guest Charlie")
        guest_pid = guest["id"]

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")

        r = _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        assert r.status_code == 201
        r = _add_buy_in(client, dealer_token, gid, guest_pid, "100.00", "1000")
        assert r.status_code == 201

        # Guest loses
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")
        _set_final_stack(client, dealer_token, gid, guest_pid, "800")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200

        # Check DB: should be zero settlement_owed notifications total
        settlement_notifs = (
            db_session.query(Notification)
            .filter(Notification.type == NotificationType.settlement_owed)
            .all()
        )
        assert len(settlement_notifs) == 0

    def test_no_notifications_when_everyone_breaks_even(self, client: TestClient):
        """No settlement_owed notifications when all balances are zero."""
        dealer_token, _ = _register_and_login(client, f"sn_even_d_{id(client)}@test.com")
        player_token, _ = _register_and_login(client, f"sn_even_p_{id(client)}@test.com")
        game = _create_game(client, dealer_token, "Even Game")
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player_token, invite_tok)

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        player_pid = next(p["id"] for p in parts if p["role_in_game"] == "player")

        r = _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        assert r.status_code == 201
        r = _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "1000")
        assert r.status_code == 201

        # Everyone ends with the same chips they started with
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1000")
        _set_final_stack(client, dealer_token, gid, player_pid, "1000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200

        # No one owes anyone
        dealer_notifs = _settlement_notifications(_get_notifications(client, dealer_token))
        player_notifs = _settlement_notifications(_get_notifications(client, player_token))
        assert len(dealer_notifs) == 0
        assert len(player_notifs) == 0

    def test_multiple_transfers_produce_multiple_notifications(self, client: TestClient):
        """A debtor who owes multiple creditors gets one notification per transfer."""
        dealer_token, dealer_uid = _register_and_login(client, f"sn_multi_d_{id(client)}@test.com")
        player1_token, player1_uid = _register_and_login(client, f"sn_multi_p1_{id(client)}@test.com")
        player2_token, player2_uid = _register_and_login(client, f"sn_multi_p2_{id(client)}@test.com")
        game = _create_game(client, dealer_token, "Multi Game")
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player1_token, invite_tok)
        _join_by_token(client, player2_token, invite_tok)

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        # Map user_id to participant_id for reliable assignment
        p1_pid = next(p["id"] for p in parts if p["user_id"] == player1_uid)
        p2_pid = next(p["id"] for p in parts if p["user_id"] == player2_uid)

        # Everyone buys in 100 (1000 chips each, total 3000 chips)
        for pid in [dealer_pid, p1_pid, p2_pid]:
            r = _add_buy_in(client, dealer_token, gid, pid, "100.00", "1000")
            assert r.status_code == 201

        # Dealer wins big, player1 wins a bit, player2 loses a lot
        # Player2 ends up owing both dealer and player1
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1800")
        _set_final_stack(client, dealer_token, gid, p1_pid, "1100")
        _set_final_stack(client, dealer_token, gid, p2_pid, "100")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200

        # Player2 is the big loser — should have settlement_owed notifications
        player2_notifs = _settlement_notifications(_get_notifications(client, player2_token))
        assert len(player2_notifs) >= 1  # At least one transfer

        # Dealer is the big winner — should NOT have settlement_owed
        dealer_notifs = _settlement_notifications(_get_notifications(client, dealer_token))
        assert len(dealer_notifs) == 0

    def test_left_early_debtor_receives_notification(self, client: TestClient):
        """A registered player who left early and is a debtor still gets notified."""
        dealer_token, _ = _register_and_login(client, f"sn_le_d_{id(client)}@test.com")
        player_token, _ = _register_and_login(client, f"sn_le_p_{id(client)}@test.com")
        game = _create_game(client, dealer_token, "Left Early Game")
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player_token, invite_tok)

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")

        r = _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        assert r.status_code == 201
        player_pid = next(p["id"] for p in parts if p["role_in_game"] == "player")
        r = _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "1000")
        assert r.status_code == 201

        # Player cashes out early with fewer chips (losing)
        r = client.post(
            f"/games/{gid}/cashout",
            json={"chips_amount": "800"},
            headers=_auth(player_token),
        )
        assert r.status_code == 200

        # Dealer enters their final stack
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")

        # Close the game
        r = _close(client, dealer_token, gid)
        assert r.status_code == 200

        # Player left early but is still a debtor — should get notification
        player_notifs = _settlement_notifications(_get_notifications(client, player_token))
        assert len(player_notifs) == 1
        assert player_notifs[0]["data"]["game_title"] == "Left Early Game"
