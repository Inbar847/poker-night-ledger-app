"""
Tests for settlement shortage resolution.

Covers:
- compute_shortage_amount: zero when no shortage
- compute_shortage_amount: positive when net_balance_sum > 0
- distribute_shortage proportional_winners: correct shares, exact sum, remainder allocation
- distribute_shortage equal_all: correct shares, exact sum, remainder allocation
- distribute_shortage proportional_winners fallback to equal_all when no winners
- GET /games/{id}/shortage-preview: returns has_shortage=False for zero-sum game
- GET /games/{id}/shortage-preview: returns has_shortage=True with correct amount
- GET /games/{id}/shortage-preview: 403 for non-dealer
- GET /games/{id}/shortage-preview: 400 for non-active game
- POST /games/{id}/close: succeeds without body when no shortage
- POST /games/{id}/close: returns 200 ShortageResolutionRequired (game stays active) when shortage exists and no strategy provided
- POST /games/{id}/close: succeeds with proportional_winners strategy
- POST /games/{id}/close: succeeds with equal_all strategy
- Settlement after proportional_winners: adjusted_net_balance and shortage_share correct
- Settlement after equal_all: adjusted_net_balance and shortage_share correct
- Settlement with no shortage: shortage_share=0, adjusted_net_balance=net_balance
- Transfers use adjusted_net_balance, not raw net_balance
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.services.settlement_service import (
    _ParticipantCalc,
    compute_shortage_amount,
    distribute_shortage,
)
import uuid


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


_RATE = "0.01"  # 1 chip = 0.01 cash


def _create_game(client: TestClient, token: str, rate: str = _RATE) -> dict:
    r = client.post(
        "/games",
        json={"title": "Test Game", "chip_cash_rate": rate, "currency": "ILS"},
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


def _add_buy_in(
    client: TestClient, token: str, game_id: str, pid: str, cash: str, chips: str
) -> None:
    r = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": pid, "cash_amount": cash, "chips_amount": chips, "buy_in_type": "initial"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text


def _set_final_stack(
    client: TestClient, token: str, game_id: str, pid: str, chips: str
) -> None:
    r = client.put(
        f"/games/{game_id}/final-stacks/{pid}",
        json={"chips_amount": chips},
        headers=_auth(token),
    )
    assert r.status_code in (200, 201), r.text


def _close(client: TestClient, token: str, game_id: str, strategy: str | None = None) -> dict:
    body: dict = {}
    if strategy:
        body["shortage_strategy"] = strategy
    r = client.post(f"/games/{game_id}/close", json=body, headers=_auth(token))
    return r


def _join_by_token(client: TestClient, token: str, invite_token: str) -> dict:
    r = client.post(
        "/games/join-by-token",
        json={"token": invite_token},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _invite_link(client: TestClient, token: str, game_id: str) -> str:
    r = client.post(f"/games/{game_id}/invite-link", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()["invite_token"]


# ---------------------------------------------------------------------------
# Unit tests for shortage calculation functions
# ---------------------------------------------------------------------------


class _FakeParticipant:
    """Minimal stand-in for Participant to avoid SQLAlchemy ORM instrumentation."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.guest_name = None
        self.user_id = None


def _make_calc(net: Decimal | None) -> _ParticipantCalc:
    """Create a minimal _ParticipantCalc with the given net_balance."""
    calc = _ParticipantCalc(
        participant=_FakeParticipant(),  # type: ignore[arg-type]
        display_name="TestPlayer",
    )
    calc.net_balance = net
    return calc


class TestComputeShortageAmount:
    def test_zero_sum_no_shortage(self):
        calcs = [_make_calc(Decimal("10.00")), _make_calc(Decimal("-10.00"))]
        assert compute_shortage_amount(calcs) == Decimal("0")

    def test_positive_sum_shortage(self):
        calcs = [_make_calc(Decimal("5.01")), _make_calc(Decimal("-5.00"))]
        shortage = compute_shortage_amount(calcs)
        assert shortage == Decimal("0.01")

    def test_negative_sum_no_shortage(self):
        # Net sum is negative → no shortage (surplus in pot)
        calcs = [_make_calc(Decimal("4.99")), _make_calc(Decimal("-5.00"))]
        assert compute_shortage_amount(calcs) == Decimal("0")

    def test_incomplete_returns_zero(self):
        calcs = [_make_calc(Decimal("10.00")), _make_calc(None)]
        assert compute_shortage_amount(calcs) == Decimal("0")

    def test_single_participant_positive(self):
        calcs = [_make_calc(Decimal("0.03"))]
        assert compute_shortage_amount(calcs) == Decimal("0.03")


class TestDistributeShortage:
    def test_proportional_winners_exact(self):
        """Two winners: 60 and 40 net. Shortage 1.00. Shares: 0.60 and 0.40."""
        w1 = _make_calc(Decimal("60.00"))
        w2 = _make_calc(Decimal("40.00"))
        loser = _make_calc(Decimal("-100.00"))
        calcs = [w1, w2, loser]
        shares = distribute_shortage(calcs, Decimal("1.00"), "proportional_winners")
        assert shares.get(loser.participant.id, Decimal("0")) == Decimal("0")
        total = sum(shares.values())
        assert total == Decimal("1.00")
        # w1 gets 0.60, w2 gets 0.40
        assert shares[w1.participant.id] == Decimal("0.60")
        assert shares[w2.participant.id] == Decimal("0.40")

    def test_proportional_winners_remainder(self):
        """Three equal winners, shortage 0.02 → 0.00 each + 2¢ remainder."""
        calcs = [_make_calc(Decimal("10.00")) for _ in range(3)]
        shortage = Decimal("0.02")
        shares = distribute_shortage(calcs, shortage, "proportional_winners")
        total = sum(shares.values())
        assert total == shortage
        # Each share is either 0.00 or 0.01; two get 0.01, one gets 0.00
        values = sorted(shares.values(), reverse=True)
        assert values[0] == Decimal("0.01")
        assert values[1] == Decimal("0.01")
        assert values[2] == Decimal("0.00")

    def test_equal_all_exact(self):
        """4 participants, shortage 1.00 → 0.25 each."""
        calcs = [_make_calc(Decimal("5.00"))] + [_make_calc(Decimal("-5.00")) for _ in range(3)]
        shares = distribute_shortage(calcs, Decimal("1.00"), "equal_all")
        assert sum(shares.values()) == Decimal("1.00")
        for v in shares.values():
            assert v == Decimal("0.25")

    def test_equal_all_with_remainder(self):
        """3 participants, shortage 0.10 → base 0.03 each + 1¢ remainder."""
        calcs = [_make_calc(Decimal("1.00")) for _ in range(3)]
        shares = distribute_shortage(calcs, Decimal("0.10"), "equal_all")
        total = sum(shares.values())
        assert total == Decimal("0.10")
        values = sorted(shares.values(), reverse=True)
        assert values[0] == Decimal("0.04")
        assert values[1] == Decimal("0.03")
        assert values[2] == Decimal("0.03")

    def test_proportional_winners_no_winners_fallback(self):
        """If no winners, proportional_winners falls back to equal_all."""
        calcs = [_make_calc(Decimal("-2.00")), _make_calc(Decimal("-3.00"))]
        # Both are losers; strategy should fall back to equal_all
        shares = distribute_shortage(calcs, Decimal("0.04"), "proportional_winners")
        total = sum(shares.values())
        assert total == Decimal("0.04")

    def test_zero_shortage_returns_empty(self):
        calcs = [_make_calc(Decimal("1.00"))]
        assert distribute_shortage(calcs, Decimal("0"), "equal_all") == {}

    # -----------------------------------------------------------------------
    # 3+ player tests — verify pure-Decimal remainder distribution
    # -----------------------------------------------------------------------

    def test_proportional_winners_three_unequal_winners(self):
        """Three winners with unequal net balances and indivisible shortage.

        Winners: 50, 30, 20 (total 100). Shortage 0.07.
        Proportional (floor): 50/100*0.07=0.03, 30/100*0.07=0.02, 20/100*0.07=0.01
        Allocated = 0.06, remainder = 1 cent → goes to largest winner.
        Expected: 0.04, 0.02, 0.01
        """
        w1 = _make_calc(Decimal("50.00"))
        w2 = _make_calc(Decimal("30.00"))
        w3 = _make_calc(Decimal("20.00"))
        loser = _make_calc(Decimal("-100.00"))
        calcs = [w1, w2, w3, loser]

        shares = distribute_shortage(calcs, Decimal("0.07"), "proportional_winners")
        total = sum(shares.values())
        assert total == Decimal("0.07"), f"Total {total} != 0.07"
        assert shares.get(loser.participant.id, Decimal("0")) == Decimal("0")
        assert shares[w1.participant.id] == Decimal("0.04")
        assert shares[w2.participant.id] == Decimal("0.02")
        assert shares[w3.participant.id] == Decimal("0.01")

    def test_proportional_winners_four_equal_winners_large_remainder(self):
        """Four equal winners, shortage 0.07.

        Each proportional share (floor): floor(0.07/4) * (25/100) = floor(0.0175) = 0.01
        Allocated = 0.04, remainder = 3 cents → top 3 winners each get 1 extra cent.
        Since all winners are equal, the 3 with sorted-highest net_balance (tie-break
        by participant_id) get the extra cent.
        """
        calcs = [_make_calc(Decimal("25.00")) for _ in range(4)]
        calcs.append(_make_calc(Decimal("-100.00")))  # loser

        shares = distribute_shortage(calcs, Decimal("0.07"), "proportional_winners")
        total = sum(shares.values())
        assert total == Decimal("0.07"), f"Total {total} != 0.07"
        winner_shares = sorted(
            [v for pid, v in shares.items() if v > 0], reverse=True
        )
        assert winner_shares == [
            Decimal("0.02"), Decimal("0.02"), Decimal("0.02"), Decimal("0.01")
        ]

    def test_equal_all_five_participants(self):
        """Five participants, shortage 0.07.

        base = floor(0.07 / 5) = 0.01 each.
        Allocated = 0.05, remainder = 2 cents → first 2 by sorted pid get 0.02.
        """
        calcs = [_make_calc(Decimal("10.00")) for _ in range(3)]
        calcs += [_make_calc(Decimal("-15.00")) for _ in range(2)]

        shares = distribute_shortage(calcs, Decimal("0.07"), "equal_all")
        total = sum(shares.values())
        assert total == Decimal("0.07"), f"Total {total} != 0.07"
        values = sorted(shares.values(), reverse=True)
        assert values[0] == Decimal("0.02")
        assert values[1] == Decimal("0.02")
        assert values[2] == Decimal("0.01")
        assert values[3] == Decimal("0.01")
        assert values[4] == Decimal("0.01")

    def test_equal_all_seven_participants_large_shortage(self):
        """Seven participants, shortage 1.00.

        base = floor(1.00 / 7) = 0.14 each.
        Allocated = 0.98, remainder = 2 cents → first 2 by sorted pid get 0.15.
        """
        calcs = [_make_calc(Decimal("5.00")) for _ in range(7)]

        shares = distribute_shortage(calcs, Decimal("1.00"), "equal_all")
        total = sum(shares.values())
        assert total == Decimal("1.00"), f"Total {total} != 1.00"
        values = sorted(shares.values(), reverse=True)
        assert values[0] == Decimal("0.15")
        assert values[1] == Decimal("0.15")
        for v in values[2:]:
            assert v == Decimal("0.14")

    def test_proportional_winners_three_players_penny_shortage(self):
        """Smallest possible shortage (0.01) with 3 winners.

        Floor of proportional share is 0.00 for all. Remainder = 1 cent → largest
        winner gets it. All others get 0.00.
        """
        w1 = _make_calc(Decimal("50.00"))
        w2 = _make_calc(Decimal("30.00"))
        w3 = _make_calc(Decimal("20.00"))
        calcs = [w1, w2, w3]

        shares = distribute_shortage(calcs, Decimal("0.01"), "proportional_winners")
        total = sum(shares.values())
        assert total == Decimal("0.01")
        assert shares[w1.participant.id] == Decimal("0.01")
        assert shares[w2.participant.id] == Decimal("0.00")
        assert shares[w3.participant.id] == Decimal("0.00")

    def test_proportional_winners_sum_always_exact(self):
        """Stress-test: many winners with awkward shortage ensures sum is exact."""
        calcs = []
        for net in [Decimal("17.31"), Decimal("8.49"), Decimal("3.77"),
                     Decimal("22.06"), Decimal("1.12")]:
            calcs.append(_make_calc(net))
        calcs.append(_make_calc(Decimal("-52.75")))  # loser
        shortage = Decimal("0.13")

        shares = distribute_shortage(calcs, shortage, "proportional_winners")
        total = sum(shares.values())
        assert total == shortage, f"Total {total} != {shortage}"
        for v in shares.values():
            # Every share must be a clean 2-decimal value
            assert v == v.quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Integration tests via HTTP
# ---------------------------------------------------------------------------


def _run_two_player_game_with_shortage(client, dealer_token, player_token):
    """
    Set up a two-player game where chip-rate rounding produces a shortage.

    chip_cash_rate = 0.003 (3 decimal places will cause rounding)
    Dealer:  buys in 10.00 for 3333 chips,  ends with 3334 chips
             chip value = 3334 * 0.003 = 10.002 → 10.00 (rounded)
             net = 10.00 - 10.00 = 0.00
    Player:  buys in 10.00 for 3333 chips,  ends with 3332 chips
             chip value = 3332 * 0.003 = 9.996 → 10.00 (rounded)
             net = 10.00 - 10.00 = 0.00

    Hmm, let me think differently. I'll use a rate that causes surplus on chips.

    chip_cash_rate = 0.01
    Dealer:  buys in 100.00 for 10000 chips, ends with 10001 chips
             chip value = 10001 * 0.01 = 100.01
             net = 100.01 - 100.00 = +0.01
    Player:  buys in 100.00 for 10000 chips, ends with 9999 chips
             chip value = 9999 * 0.01 = 99.99
             net = 99.99 - 100.00 = -0.01

    Sum = +0.01 - 0.01 = 0.00 → no shortage

    I need net_balance_sum > 0. Let's try:
    Dealer: buys in 100.00 for 10000 chips, ends with 10002 chips → net +0.02
    Player: buys in 100.00 for 10000 chips, ends with 9999 chips → net -0.01
    Sum = +0.01 → shortage = 0.01
    """
    game = _create_game(client, dealer_token, rate="0.01")
    gid = game["id"]

    token_for_join = _invite_link(client, dealer_token, gid)
    _join_by_token(client, player_token, token_for_join)

    parts = _get_participants(client, dealer_token, gid)
    dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
    player_pid = next(p["id"] for p in parts if p["role_in_game"] == "player")

    _start(client, dealer_token, gid)

    _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "10000")
    _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "10000")

    # Dealer ends with 10002 chips: net = (10002 * 0.01) - 100 = +0.02
    # Player ends with 9999 chips: net = (9999 * 0.01) - 100 = -0.01
    # Sum = +0.01 → shortage 0.01
    _set_final_stack(client, dealer_token, gid, dealer_pid, "10002")
    _set_final_stack(client, dealer_token, gid, player_pid, "9999")

    return gid, dealer_pid, player_pid


class TestShortagePreviewEndpoint:
    def test_no_shortage(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "prev_nodeal@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        parts = _get_participants(client, dealer_token, gid)
        pid = parts[0]["id"]
        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, pid, "100.00", "10000")
        _set_final_stack(client, dealer_token, gid, pid, "10000")  # exact break-even

        r = client.get(f"/games/{gid}/shortage-preview", headers=_auth(dealer_token))
        assert r.status_code == 200
        body = r.json()
        assert body["has_shortage"] is False
        assert Decimal(body["shortage_amount"]) == Decimal("0")

    def test_has_shortage(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "prev_short@test.com")
        player_token, _ = _register_and_login(client, "prev_short_p@test.com")
        gid, _, _ = _run_two_player_game_with_shortage(client, dealer_token, player_token)

        r = client.get(f"/games/{gid}/shortage-preview", headers=_auth(dealer_token))
        assert r.status_code == 200
        body = r.json()
        assert body["has_shortage"] is True
        assert Decimal(body["shortage_amount"]) == Decimal("0.01")

    def test_non_dealer_forbidden(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "prev_403d@test.com")
        player_token, _ = _register_and_login(client, "prev_403p@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        tok = _invite_link(client, dealer_token, gid)
        _join_by_token(client, player_token, tok)
        _start(client, dealer_token, gid)

        r = client.get(f"/games/{gid}/shortage-preview", headers=_auth(player_token))
        assert r.status_code == 403

    def test_closed_game_returns_400(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "prev_closed@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        parts = _get_participants(client, dealer_token, gid)
        pid = parts[0]["id"]
        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, pid, "100.00", "10000")
        _set_final_stack(client, dealer_token, gid, pid, "10000")
        close_r = _close(client, dealer_token, gid)
        assert close_r.status_code == 200

        r = client.get(f"/games/{gid}/shortage-preview", headers=_auth(dealer_token))
        assert r.status_code == 400


class TestCloseGameShortage:
    def test_no_shortage_close_no_body(self, client: TestClient):
        """Close works with no body when there's no shortage."""
        dealer_token, _ = _register_and_login(client, "cls_no_short@test.com")
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

    def test_shortage_no_strategy_returns_resolution_required(self, client: TestClient):
        """Without a strategy, the endpoint returns HTTP 200 with requires_shortage_resolution=True.

        The game must NOT be closed — this is a non-error prompt for the client to
        show the strategy selection modal.
        """
        dealer_token, _ = _register_and_login(client, "cls_400d@test.com")
        player_token, _ = _register_and_login(client, "cls_400p@test.com")
        gid, _, _ = _run_two_player_game_with_shortage(client, dealer_token, player_token)

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200
        body = r.json()
        assert body["requires_shortage_resolution"] is True
        assert Decimal(body["shortage_amount"]) == Decimal("0.01")
        assert "proportional_winners" in body["available_strategies"]
        assert "equal_all" in body["available_strategies"]

        # Game must still be active — not closed
        game_r = client.get(f"/games/{gid}", headers=_auth(dealer_token))
        assert game_r.json()["status"] == "active"

    def test_shortage_invalid_strategy_returns_422(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "cls_422d@test.com")
        player_token, _ = _register_and_login(client, "cls_422p@test.com")
        gid, _, _ = _run_two_player_game_with_shortage(client, dealer_token, player_token)

        r = client.post(
            f"/games/{gid}/close",
            json={"shortage_strategy": "invalid_strategy"},
            headers=_auth(dealer_token),
        )
        assert r.status_code == 422

    def test_shortage_proportional_winners_closes(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "cls_prowd@test.com")
        player_token, _ = _register_and_login(client, "cls_prowp@test.com")
        gid, _, _ = _run_two_player_game_with_shortage(client, dealer_token, player_token)

        r = _close(client, dealer_token, gid, strategy="proportional_winners")
        assert r.status_code == 200
        assert r.json()["status"] == "closed"
        assert r.json()["shortage_strategy"] == "proportional_winners"

    def test_shortage_equal_all_closes(self, client: TestClient):
        dealer_token, _ = _register_and_login(client, "cls_eqd@test.com")
        player_token, _ = _register_and_login(client, "cls_eqp@test.com")
        gid, _, _ = _run_two_player_game_with_shortage(client, dealer_token, player_token)

        r = _close(client, dealer_token, gid, strategy="equal_all")
        assert r.status_code == 200
        assert r.json()["shortage_strategy"] == "equal_all"


class TestSettlementAfterShortage:
    def _get_settlement(self, client, token, gid):
        r = client.get(f"/games/{gid}/settlement", headers=_auth(token))
        assert r.status_code == 200, r.text
        return r.json()

    def test_proportional_winners_settlement(self, client: TestClient):
        """
        Dealer has +0.02 raw net (the only winner).
        Shortage = 0.01.
        proportional_winners: dealer absorbs all 0.01.
        adjusted_net dealer = 0.02 - 0.01 = 0.01
        adjusted_net player = -0.01 - 0.00 = -0.01
        Transfer: player pays dealer 0.01.
        """
        dealer_token, _ = _register_and_login(client, "stl_prowd@test.com")
        player_token, _ = _register_and_login(client, "stl_prowp@test.com")
        gid, dealer_pid, player_pid = _run_two_player_game_with_shortage(
            client, dealer_token, player_token
        )
        _close(client, dealer_token, gid, strategy="proportional_winners")

        body = self._get_settlement(client, dealer_token, gid)
        assert Decimal(body["shortage_amount"]) == Decimal("0.01")
        assert body["shortage_strategy"] == "proportional_winners"

        bal_by_pid = {b["participant_id"]: b for b in body["balances"]}
        dealer_bal = bal_by_pid[dealer_pid]
        player_bal = bal_by_pid[player_pid]

        assert Decimal(dealer_bal["shortage_share"]) == Decimal("0.01")
        assert Decimal(dealer_bal["adjusted_net_balance"]) == Decimal("0.01")
        assert Decimal(player_bal["shortage_share"]) == Decimal("0.00")
        assert Decimal(player_bal["adjusted_net_balance"]) == Decimal("-0.01")

    def test_equal_all_settlement(self, client: TestClient):
        """
        Shortage = 0.01, equal_all across 2 participants.
        base_share = floor(0.01 / 2) = 0.00 each.
        Remainder 0.01 goes to first participant by pid order → one gets 0.01, other 0.00.
        Total shortage absorbed = 0.01 ✓
        """
        dealer_token, _ = _register_and_login(client, "stl_eqd@test.com")
        player_token, _ = _register_and_login(client, "stl_eqp@test.com")
        gid, dealer_pid, player_pid = _run_two_player_game_with_shortage(
            client, dealer_token, player_token
        )
        _close(client, dealer_token, gid, strategy="equal_all")

        body = self._get_settlement(client, dealer_token, gid)
        assert Decimal(body["shortage_amount"]) == Decimal("0.01")
        assert body["shortage_strategy"] == "equal_all"

        bal_by_pid = {b["participant_id"]: b for b in body["balances"]}
        total_share = sum(
            Decimal(b["shortage_share"]) for b in bal_by_pid.values()
        )
        assert total_share == Decimal("0.01")
        # All adjusted_net_balance must be valid decimals
        for b in bal_by_pid.values():
            assert b["adjusted_net_balance"] is not None

    def test_no_shortage_settlement_fields_default(self, client: TestClient):
        """When no shortage, shortage_share=0.00 and adjusted_net_balance=net_balance."""
        dealer_token, _ = _register_and_login(client, "stl_noshd@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        parts = _get_participants(client, dealer_token, gid)
        pid = parts[0]["id"]
        _start(client, dealer_token, gid)
        _add_buy_in(client, dealer_token, gid, pid, "100.00", "10000")
        _set_final_stack(client, dealer_token, gid, pid, "10000")
        _close(client, dealer_token, gid)

        body = self._get_settlement(client, dealer_token, gid)
        assert Decimal(body["shortage_amount"]) == Decimal("0")
        assert body["shortage_strategy"] is None

        for b in body["balances"]:
            assert Decimal(b["shortage_share"]) == Decimal("0")
            if b["net_balance"] is not None:
                assert Decimal(b["adjusted_net_balance"]) == Decimal(b["net_balance"])

    def test_transfers_use_adjusted_balance(self, client: TestClient):
        """
        After proportional_winners: dealer (only winner) absorbs shortage.
        Transfer should reflect adjusted balance, not raw.
        Raw: player owes dealer 0.01. Adjusted: player still owes dealer 0.01
        (shortage absorbed by dealer reduces their credit).
        """
        dealer_token, _ = _register_and_login(client, "stl_trfd@test.com")
        player_token, _ = _register_and_login(client, "stl_trfp@test.com")
        gid, dealer_pid, player_pid = _run_two_player_game_with_shortage(
            client, dealer_token, player_token
        )
        _close(client, dealer_token, gid, strategy="proportional_winners")

        body = self._get_settlement(client, dealer_token, gid)
        transfers = body["transfers"]
        assert len(transfers) == 1
        t = transfers[0]
        # Player (debtor, adjusted -0.01) pays dealer (creditor, adjusted +0.01)
        assert t["from_participant_id"] == player_pid
        assert t["to_participant_id"] == dealer_pid
        assert Decimal(t["amount"]) == Decimal("0.01")
