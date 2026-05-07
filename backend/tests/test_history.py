"""
Tests for Stage 8: history and personal statistics.

Covers:
- Empty history returns []
- Lobby/active game NOT included in history
- Closed game appears in history for participant
- Closed game absent for non-participant
- History item has correct role_in_game (dealer vs player)
- net_balance is None when participant has no final stack
- net_balance is correct when final stack exists
- GET /history/games/{id} returns 404 for non-participant
- GET /history/games/{id} returns settlement for participant
- Stats return zeros for user with no games
- Stats count games_played and games_hosted correctly
- Stats compute cumulative_net and win_rate correctly
- Stats recent_games limited to 5
- Auth required (401 for unauthenticated)
"""

from decimal import Decimal

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared helpers (mirrored from other test files)
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, email: str, password: str = "pw12345678") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_RATE = 0.01  # 1 chip = $0.01


def _create_game(client: TestClient, token: str, rate: float = _RATE) -> dict:
    r = client.post(
        "/games",
        json={"title": "Test Game", "chip_cash_rate": rate, "currency": "USD"},
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


def _close(client: TestClient, token: str, game_id: str) -> None:
    r = client.post(
        f"/games/{game_id}/close",
        json={"shortage_strategy": "equal_all"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text


def _add_buy_in(
    client: TestClient,
    token: str,
    game_id: str,
    participant_id: str,
    cash: float,
    chips: float,
) -> None:
    r = client.post(
        f"/games/{game_id}/buy-ins",
        json={
            "participant_id": participant_id,
            "cash_amount": str(cash),
            "chips_amount": str(chips),
            "buy_in_type": "initial",
        },
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text


def _set_final_stack(
    client: TestClient, token: str, game_id: str, participant_id: str, chips: float
) -> None:
    r = client.put(
        f"/games/{game_id}/final-stacks/{participant_id}",
        json={"chips_amount": str(chips)},
        headers=_auth(token),
    )
    assert r.status_code in (200, 201), r.text


def _join(client: TestClient, token: str, invite_token: str) -> dict:
    r = client.post(
        "/games/join-by-token",
        json={"token": invite_token},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _generate_invite(client: TestClient, token: str, game_id: str) -> str:
    r = client.post(f"/games/{game_id}/invite-link", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()["invite_token"]


def _run_full_game(
    client: TestClient,
    dealer_token: str,
    dealer_participant_id: str,
    game_id: str,
    cash_in: float,
    chips_in: float,
    final_chips: float,
) -> None:
    """Start a game, add one buy-in and final stack for the dealer, then close it."""
    _start(client, dealer_token, game_id)
    _add_buy_in(client, dealer_token, game_id, dealer_participant_id, cash_in, chips_in)
    _set_final_stack(client, dealer_token, game_id, dealer_participant_id, final_chips)
    _close(client, dealer_token, game_id)


# ---------------------------------------------------------------------------
# Tests: GET /history/games
# ---------------------------------------------------------------------------


class TestListHistory:
    def test_empty_history(self, client: TestClient) -> None:
        token = _register_and_login(client, "hist_empty@test.com")
        r = client.get("/history/games", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_lobby_game_excluded(self, client: TestClient) -> None:
        token = _register_and_login(client, "hist_lobby@test.com")
        _create_game(client, token)
        r = client.get("/history/games", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_active_game_excluded(self, client: TestClient) -> None:
        token = _register_and_login(client, "hist_active@test.com")
        game = _create_game(client, token)
        _start(client, token, game["id"])
        r = client.get("/history/games", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_closed_game_appears(self, client: TestClient) -> None:
        token = _register_and_login(client, "hist_closed@test.com")
        game = _create_game(client, token)
        participants = _get_participants(client, token, game["id"])
        dealer_pid = participants[0]["id"]
        _run_full_game(client, token, dealer_pid, game["id"], 100, 10000, 10000)

        r = client.get("/history/games", headers=_auth(token))
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["game_id"] == game["id"]
        assert items[0]["title"] == "Test Game"
        assert items[0]["role_in_game"] == "dealer"

    def test_closed_game_absent_for_non_participant(self, client: TestClient) -> None:
        t1 = _register_and_login(client, "hist_np_dealer@test.com")
        t2 = _register_and_login(client, "hist_np_other@test.com")
        game = _create_game(client, t1)
        participants = _get_participants(client, t1, game["id"])
        _run_full_game(client, t1, participants[0]["id"], game["id"], 100, 10000, 10000)

        r = client.get("/history/games", headers=_auth(t2))
        assert r.status_code == 200
        assert r.json() == []

    def test_role_in_game_player(self, client: TestClient) -> None:
        t_dealer = _register_and_login(client, "hist_role_dealer@test.com")
        t_player = _register_and_login(client, "hist_role_player@test.com")

        game = _create_game(client, t_dealer)
        invite = _generate_invite(client, t_dealer, game["id"])
        player_participant = _join(client, t_player, invite)

        participants = _get_participants(client, t_dealer, game["id"])
        dealer_pid = next(p["id"] for p in participants if p["role_in_game"] == "dealer")
        player_pid = player_participant["id"]

        _start(client, t_dealer, game["id"])
        _add_buy_in(client, t_dealer, game["id"], dealer_pid, 100, 10000)
        _add_buy_in(client, t_dealer, game["id"], player_pid, 50, 5000)
        _set_final_stack(client, t_dealer, game["id"], dealer_pid, 10000)
        _set_final_stack(client, t_dealer, game["id"], player_pid, 5000)
        _close(client, t_dealer, game["id"])

        r = client.get("/history/games", headers=_auth(t_player))
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["role_in_game"] == "player"

    def test_close_blocked_without_final_stack(self, client: TestClient) -> None:
        """Closing a game without final stacks is now blocked (returns 400)."""
        token = _register_and_login(client, "hist_no_stack@test.com")
        game = _create_game(client, token)
        participants = _get_participants(client, token, game["id"])
        dealer_pid = participants[0]["id"]
        _start(client, token, game["id"])
        _add_buy_in(client, token, game["id"], dealer_pid, 100, 10000)
        # Intentionally omit final stack
        r = client.post(
            f"/games/{game['id']}/close",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 400
        body = r.json()
        assert "missing_final_stacks" in body
        assert body["missing_final_stacks"][0]["participant_id"] == dealer_pid

    def test_net_balance_computed_correctly(self, client: TestClient) -> None:
        """
        Dealer buys in for $100 (10000 chips at rate 0.01).
        Final chips = 12000, so chip value = 120.00.
        poker_balance = 120 - 100 = +20.00.
        No expenses, so net_balance = +20.00.
        """
        token = _register_and_login(client, "hist_net@test.com")
        game = _create_game(client, token, rate=0.01)
        participants = _get_participants(client, token, game["id"])
        dealer_pid = participants[0]["id"]
        _start(client, token, game["id"])
        _add_buy_in(client, token, game["id"], dealer_pid, 100, 10000)
        _set_final_stack(client, token, game["id"], dealer_pid, 12000)
        _close(client, token, game["id"])

        r = client.get("/history/games", headers=_auth(token))
        items = r.json()
        assert items[0]["net_balance"] == "20.00"
        assert items[0]["total_buy_ins"] == "100.00"

    def test_multiple_games_ordered_by_closed_at_desc(self, client: TestClient) -> None:
        token = _register_and_login(client, "hist_order@test.com")
        # Create and close two games
        game1 = _create_game(client, token)
        p1 = _get_participants(client, token, game1["id"])[0]["id"]
        _start(client, token, game1["id"])
        _add_buy_in(client, token, game1["id"], p1, 100, 10000)
        _set_final_stack(client, token, game1["id"], p1, 10000)
        _close(client, token, game1["id"])

        game2 = _create_game(client, token)
        p2 = _get_participants(client, token, game2["id"])[0]["id"]
        _start(client, token, game2["id"])
        _add_buy_in(client, token, game2["id"], p2, 50, 5000)
        _set_final_stack(client, token, game2["id"], p2, 5000)
        _close(client, token, game2["id"])

        r = client.get("/history/games", headers=_auth(token))
        items = r.json()
        assert len(items) == 2
        # Most recently closed should be first
        assert items[0]["game_id"] == game2["id"]
        assert items[1]["game_id"] == game1["id"]

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        r = client.get("/history/games")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests: GET /history/games/{game_id}
# ---------------------------------------------------------------------------


class TestGetHistoryGame:
    def test_returns_settlement_for_participant(self, client: TestClient) -> None:
        token = _register_and_login(client, "hg_participant@test.com")
        game = _create_game(client, token)
        participants = _get_participants(client, token, game["id"])
        dealer_pid = participants[0]["id"]
        _run_full_game(client, token, dealer_pid, game["id"], 100, 10000, 12000)

        r = client.get(f"/history/games/{game['id']}", headers=_auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["game_id"] == game["id"]
        assert data["is_complete"] is True
        assert len(data["balances"]) == 1
        assert data["balances"][0]["net_balance"] == "20.00"

    def test_returns_404_for_non_participant(self, client: TestClient) -> None:
        t1 = _register_and_login(client, "hg_dealer@test.com")
        t2 = _register_and_login(client, "hg_stranger@test.com")
        game = _create_game(client, t1)
        participants = _get_participants(client, t1, game["id"])
        _run_full_game(client, t1, participants[0]["id"], game["id"], 100, 10000, 10000)

        r = client.get(f"/history/games/{game['id']}", headers=_auth(t2))
        assert r.status_code == 404

    def test_returns_404_for_active_game(self, client: TestClient) -> None:
        token = _register_and_login(client, "hg_active@test.com")
        game = _create_game(client, token)
        _start(client, token, game["id"])

        r = client.get(f"/history/games/{game['id']}", headers=_auth(token))
        assert r.status_code == 404

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        r = client.get("/history/games/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests: GET /stats/me
# ---------------------------------------------------------------------------


class TestGetStats:
    def test_empty_stats_for_new_user(self, client: TestClient) -> None:
        token = _register_and_login(client, "stats_empty@test.com")
        r = client.get("/stats/me", headers=_auth(token))
        assert r.status_code == 200
        data = r.json()
        assert data["total_games_played"] == 0
        assert data["total_games_hosted"] == 0
        assert data["games_with_result"] == 0
        assert data["cumulative_net"] == "0"
        assert data["average_net"] is None
        assert data["profitable_games"] == 0
        assert data["win_rate"] is None
        assert data["recent_games"] == []

    def test_active_games_excluded_from_stats(self, client: TestClient) -> None:
        token = _register_and_login(client, "stats_active@test.com")
        game = _create_game(client, token)
        _start(client, token, game["id"])

        r = client.get("/stats/me", headers=_auth(token))
        data = r.json()
        assert data["total_games_played"] == 0

    def test_games_played_and_hosted_counts(self, client: TestClient) -> None:
        t_dealer = _register_and_login(client, "stats_counts_dealer@test.com")
        t_player = _register_and_login(client, "stats_counts_player@test.com")

        # Game 1: dealer hosts, player joins
        game1 = _create_game(client, t_dealer)
        invite = _generate_invite(client, t_dealer, game1["id"])
        player_p = _join(client, t_player, invite)
        parts1 = _get_participants(client, t_dealer, game1["id"])
        dealer_p1 = next(p["id"] for p in parts1 if p["role_in_game"] == "dealer")

        _start(client, t_dealer, game1["id"])
        _add_buy_in(client, t_dealer, game1["id"], dealer_p1, 100, 10000)
        _add_buy_in(client, t_dealer, game1["id"], player_p["id"], 50, 5000)
        _set_final_stack(client, t_dealer, game1["id"], dealer_p1, 10000)
        _set_final_stack(client, t_dealer, game1["id"], player_p["id"], 5000)
        _close(client, t_dealer, game1["id"])

        # Dealer stats
        r = client.get("/stats/me", headers=_auth(t_dealer))
        data = r.json()
        assert data["total_games_played"] == 1
        assert data["total_games_hosted"] == 1

        # Player stats
        r = client.get("/stats/me", headers=_auth(t_player))
        data = r.json()
        assert data["total_games_played"] == 1
        assert data["total_games_hosted"] == 0

    def test_cumulative_net_and_win_rate(self, client: TestClient) -> None:
        """
        Two games:
          Game 1: buy-in $100, 10000 chips, final 12000 chips → net = +$20
          Game 2: buy-in $100, 10000 chips, final 8000 chips  → net = -$20
        cumulative_net = 0, games_with_result = 2, profitable_games = 1, win_rate = 0.5
        """
        token = _register_and_login(client, "stats_net@test.com")

        for final_chips, _ in [(12000, "+20"), (8000, "-20")]:
            game = _create_game(client, token, rate=0.01)
            p = _get_participants(client, token, game["id"])[0]["id"]
            _start(client, token, game["id"])
            _add_buy_in(client, token, game["id"], p, 100, 10000)
            _set_final_stack(client, token, game["id"], p, final_chips)
            _close(client, token, game["id"])

        r = client.get("/stats/me", headers=_auth(token))
        data = r.json()
        assert data["total_games_played"] == 2
        assert data["games_with_result"] == 2
        assert Decimal(data["cumulative_net"]) == Decimal("0.00")
        assert Decimal(data["average_net"]) == Decimal("0.00")
        assert data["profitable_games"] == 1
        assert data["win_rate"] == 0.5

    def test_close_blocked_without_final_stack_for_stats(self, client: TestClient) -> None:
        """Closing a game without final stacks is blocked, so stats remain empty."""
        token = _register_and_login(client, "stats_nostack@test.com")
        game = _create_game(client, token)
        p = _get_participants(client, token, game["id"])[0]["id"]
        _start(client, token, game["id"])
        _add_buy_in(client, token, game["id"], p, 100, 10000)
        # No final stack — close should be blocked
        r = client.post(
            f"/games/{game['id']}/close",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 400

        # Stats should show no games since none were closed
        r = client.get("/stats/me", headers=_auth(token))
        data = r.json()
        assert data["total_games_played"] == 0

    def test_recent_games_limited_to_five(self, client: TestClient) -> None:
        token = _register_and_login(client, "stats_recent@test.com")

        for _ in range(6):
            game = _create_game(client, token)
            p = _get_participants(client, token, game["id"])[0]["id"]
            _start(client, token, game["id"])
            _add_buy_in(client, token, game["id"], p, 50, 5000)
            _set_final_stack(client, token, game["id"], p, 5000)
            _close(client, token, game["id"])

        r = client.get("/stats/me", headers=_auth(token))
        data = r.json()
        assert data["total_games_played"] == 6
        assert len(data["recent_games"]) == 5

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        r = client.get("/stats/me")
        assert r.status_code == 401
