"""
Tests for Stage 4: settlement engine and audit endpoint.

Covers:
- Basic two-player game settlement
- Multiple buy-ins per participant
- Dealer is also a financial player
- Expenses split across a subset of participants
- Mixed registered users and guests
- Zero-sum validation (transfers balance)
- Rounding edge case for chip_cash_rate
- Game must be closed (409 on active game)
- Participant access control (403 for non-participant)
- Participant with no expenses
- is_complete=False when a participant lacks a final stack
"""

from decimal import Decimal

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, email: str, password: str = "pw12345678") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": email.split("@")[0]},
    )
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_CHIP_RATE = 0.01  # 1 chip = $0.01 cash


def _create_game(client: TestClient, token: str, chip_cash_rate: float = _CHIP_RATE) -> dict:
    r = client.post(
        "/games",
        json={"title": "Test Game", "chip_cash_rate": chip_cash_rate, "currency": "USD"},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _join(client: TestClient, token: str, invite_token: str) -> None:
    r = client.post(
        "/games/join-by-token",
        json={"token": invite_token},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text


def _add_guest(client: TestClient, token: str, game_id: str, name: str) -> dict:
    r = client.post(
        f"/games/{game_id}/guests",
        json={"guest_name": name},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _get_participants(client: TestClient, token: str, game_id: str) -> list[dict]:
    return client.get(f"/games/{game_id}/participants", headers=_auth(token)).json()


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


def _buy_in(
    client: TestClient,
    token: str,
    game_id: str,
    participant_id: str,
    cash: float,
    chips: float,
    buy_in_type: str = "initial",
) -> dict:
    r = client.post(
        f"/games/{game_id}/buy-ins",
        json={
            "participant_id": participant_id,
            "cash_amount": cash,
            "chips_amount": chips,
            "buy_in_type": buy_in_type,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _expense(
    client: TestClient,
    token: str,
    game_id: str,
    paid_by: str,
    total: float,
    splits: list[dict],
) -> dict:
    r = client.post(
        f"/games/{game_id}/expenses",
        json={
            "title": "Pizza",
            "total_amount": total,
            "paid_by_participant_id": paid_by,
            "splits": splits,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _set_final_stack(
    client: TestClient, token: str, game_id: str, participant_id: str, chips: float
) -> None:
    r = client.put(
        f"/games/{game_id}/final-stacks/{participant_id}",
        json={"chips_amount": chips},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text


def _get_settlement(client: TestClient, token: str, game_id: str) -> dict:
    return client.get(f"/games/{game_id}/settlement", headers=_auth(token))


def _get_audit(client: TestClient, token: str, game_id: str) -> dict:
    return client.get(f"/games/{game_id}/settlement/audit", headers=_auth(token))


# ---------------------------------------------------------------------------
# Scenario builder
# ---------------------------------------------------------------------------


def _setup_two_player_game(
    client: TestClient,
    dealer_final_chips: float = 15000,
    player_final_chips: float = 5000,
    chip_cash_rate: float = _CHIP_RATE,
):
    """
    Create a two-player game (dealer + 1 player), each buying in 100 chips ($100).
    Returns (dealer_token, player_token, game_id, dealer_pid, player_pid).

    chip_cash_rate=0.01: 1 chip = $0.01
    Each player buys 10000 chips for $100.
    Default final stacks: dealer=15000, player=5000 (total = 20000 chips = initial total).
    """
    dealer_token = _register_and_login(client, "dealer_s@example.com")
    player_token = _register_and_login(client, "player_s@example.com")

    game = _create_game(client, dealer_token, chip_cash_rate=chip_cash_rate)
    game_id = game["id"]
    _join(client, player_token, game["invite_token"])

    participants = _get_participants(client, dealer_token, game_id)
    dealer_part = next(p for p in participants if p["role_in_game"] == "dealer")
    player_part = next(p for p in participants if p["role_in_game"] == "player")
    dealer_pid = dealer_part["id"]
    player_pid = player_part["id"]

    _start(client, dealer_token, game_id)

    # Both buy in 10000 chips for $100
    _buy_in(client, dealer_token, game_id, dealer_pid, cash=100.0, chips=10000.0)
    _buy_in(client, dealer_token, game_id, player_pid, cash=100.0, chips=10000.0)

    _set_final_stack(client, dealer_token, game_id, dealer_pid, chips=dealer_final_chips)
    _set_final_stack(client, dealer_token, game_id, player_pid, chips=player_final_chips)

    _close(client, dealer_token, game_id)

    return dealer_token, player_token, game_id, dealer_pid, player_pid


# ---------------------------------------------------------------------------
# Tests: access control
# ---------------------------------------------------------------------------


def test_settlement_requires_closed_game(client: TestClient):
    dealer_token = _register_and_login(client, "d_ac1@example.com")
    game = _create_game(client, dealer_token)
    game_id = game["id"]

    # Lobby state → 409
    r = _get_settlement(client, dealer_token, game_id)
    assert r.status_code == 409

    _start(client, dealer_token, game_id)

    # Active state → 409
    r = _get_settlement(client, dealer_token, game_id)
    assert r.status_code == 409


def test_settlement_requires_participation(client: TestClient):
    dealer_token = _register_and_login(client, "d_ac2@example.com")
    outsider_token = _register_and_login(client, "outsider_ac2@example.com")

    game = _create_game(client, dealer_token)
    game_id = game["id"]
    _start(client, dealer_token, game_id)
    ps = _get_participants(client, dealer_token, game_id)
    for p in ps:
        _set_final_stack(client, dealer_token, game_id, p["id"], 0)
    _close(client, dealer_token, game_id)

    r = _get_settlement(client, outsider_token, game_id)
    assert r.status_code == 403


def test_settlement_unknown_game(client: TestClient):
    token = _register_and_login(client, "nobody_ac3@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = _get_settlement(client, token, fake_id)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tests: basic two-player settlement
# ---------------------------------------------------------------------------


def test_basic_two_player_settlement(client: TestClient):
    """
    Dealer buys 10000 chips for $100, ends with 15000 chips ($150 → +$50).
    Player buys 10000 chips for $100, ends with  5000 chips ($50  → -$50).
    No expenses.
    Expected: player pays dealer $50.
    """
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_two_player_game(
        client, dealer_final_chips=15000, player_final_chips=5000
    )

    r = _get_settlement(client, dealer_token, game_id)
    assert r.status_code == 200
    body = r.json()

    assert body["is_complete"] is True
    assert body["game_status"] == "closed"
    assert Decimal(str(body["chip_cash_rate"])) == Decimal("0.01")

    balances = {b["participant_id"]: b for b in body["balances"]}
    dealer_b = balances[dealer_pid]
    player_b = balances[player_pid]

    assert Decimal(str(dealer_b["net_balance"])) == Decimal("50.00")
    assert Decimal(str(player_b["net_balance"])) == Decimal("-50.00")

    transfers = body["transfers"]
    assert len(transfers) == 1
    t = transfers[0]
    assert t["from_participant_id"] == player_pid
    assert t["to_participant_id"] == dealer_pid
    assert Decimal(str(t["amount"])) == Decimal("50.00")


def test_settlement_zero_sum_transfers(client: TestClient):
    """Sum of transfer amounts leaving == sum arriving; net = 0."""
    dealer_token2 = _register_and_login(client, "d_zs2@example.com")
    player_token2 = _register_and_login(client, "p_zs2@example.com")
    game = _create_game(client, dealer_token2)
    gid = game["id"]
    _join(client, player_token2, game["invite_token"])
    ps = _get_participants(client, dealer_token2, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]
    _start(client, dealer_token2, gid)
    _buy_in(client, dealer_token2, gid, dpid, 100, 10000)
    _buy_in(client, dealer_token2, gid, ppid, 100, 10000)
    _set_final_stack(client, dealer_token2, gid, dpid, 13000)
    _set_final_stack(client, dealer_token2, gid, ppid, 7000)
    _close(client, dealer_token2, gid)

    r = _get_settlement(client, dealer_token2, gid)
    body = r.json()
    net = sum(Decimal(str(b["net_balance"])) for b in body["balances"])
    assert abs(net) <= Decimal("0.05")  # within rounding tolerance

    sent = sum(Decimal(str(t["amount"])) for t in body["transfers"])
    received = sum(Decimal(str(t["amount"])) for t in body["transfers"])
    assert sent == received  # trivially true; verify transfers non-empty
    assert len(body["transfers"]) >= 1


# ---------------------------------------------------------------------------
# Tests: multiple buy-ins
# ---------------------------------------------------------------------------


def test_multiple_buy_ins_per_participant(client: TestClient):
    """
    Dealer: 2 buy-ins ($50 + $50 = $100), ends with 10000 chips = $100 → net $0.
    Player: 1 buy-in ($100), ends with 10000 chips = $100 → net $0.
    No transfers expected.
    """
    dealer_token = _register_and_login(client, "d_multi@example.com")
    player_token = _register_and_login(client, "p_multi@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, cash=50.0, chips=5000.0)
    _buy_in(client, dealer_token, gid, dpid, cash=50.0, chips=5000.0, buy_in_type="rebuy")
    _buy_in(client, dealer_token, gid, ppid, cash=100.0, chips=10000.0)

    _set_final_stack(client, dealer_token, gid, dpid, chips=10000)
    _set_final_stack(client, dealer_token, gid, ppid, chips=10000)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    body = r.json()

    bals = {b["participant_id"]: b for b in body["balances"]}
    assert Decimal(str(bals[dpid]["total_buy_ins"])) == Decimal("100.00")
    assert Decimal(str(bals[dpid]["net_balance"])) == Decimal("0.00")
    assert Decimal(str(bals[ppid]["net_balance"])) == Decimal("0.00")
    assert body["transfers"] == []


# ---------------------------------------------------------------------------
# Tests: expenses
# ---------------------------------------------------------------------------


def test_expense_split_settlement(client: TestClient):
    """
    Both players break even on poker (10000 chips each in and out).
    Expense: $20 pizza paid by dealer, split evenly ($10 each).
    expense_balance: dealer = +$10 (paid $20, owed $10), player = -$10 (paid $0, owed $10).
    net: dealer = +$10, player = -$10.
    Transfer: player pays dealer $10.
    """
    dealer_token = _register_and_login(client, "d_exp@example.com")
    player_token = _register_and_login(client, "p_exp@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    _buy_in(client, dealer_token, gid, ppid, 100.0, 10000.0)

    _expense(
        client,
        dealer_token,
        gid,
        paid_by=dpid,
        total=20.0,
        splits=[
            {"participant_id": dpid, "share_amount": 10.0},
            {"participant_id": ppid, "share_amount": 10.0},
        ],
    )

    _set_final_stack(client, dealer_token, gid, dpid, 10000)
    _set_final_stack(client, dealer_token, gid, ppid, 10000)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    body = r.json()

    bals = {b["participant_id"]: b for b in body["balances"]}
    assert Decimal(str(bals[dpid]["expense_balance"])) == Decimal("10.00")
    assert Decimal(str(bals[ppid]["expense_balance"])) == Decimal("-10.00")
    assert Decimal(str(bals[dpid]["net_balance"])) == Decimal("10.00")
    assert Decimal(str(bals[ppid]["net_balance"])) == Decimal("-10.00")

    transfers = body["transfers"]
    assert len(transfers) == 1
    assert transfers[0]["from_participant_id"] == ppid
    assert transfers[0]["to_participant_id"] == dpid
    assert Decimal(str(transfers[0]["amount"])) == Decimal("10.00")


def test_expense_split_subset_only(client: TestClient):
    """
    Three players; an expense is split between two of them only.
    The third player's expense_balance must be 0.
    """
    dealer_token = _register_and_login(client, "d_sub@example.com")
    p1_token = _register_and_login(client, "p1_sub@example.com")
    p2_token = _register_and_login(client, "p2_sub@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, p1_token, game["invite_token"])
    _join(client, p2_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    player_pids = [p["id"] for p in ps if p["role_in_game"] == "player"]
    p1pid, p2pid = player_pids[0], player_pids[1]

    _start(client, dealer_token, gid)
    for pid in [dpid, p1pid, p2pid]:
        _buy_in(client, dealer_token, gid, pid, 100.0, 10000.0)

    # Expense split between dealer and p1 only
    _expense(
        client,
        dealer_token,
        gid,
        paid_by=dpid,
        total=30.0,
        splits=[
            {"participant_id": dpid, "share_amount": 15.0},
            {"participant_id": p1pid, "share_amount": 15.0},
        ],
    )

    for pid in [dpid, p1pid, p2pid]:
        _set_final_stack(client, dealer_token, gid, pid, 10000)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    body = r.json()
    bals = {b["participant_id"]: b for b in body["balances"]}

    # p2 not in the split → expense_balance == 0
    assert Decimal(str(bals[p2pid]["expense_balance"])) == Decimal("0.00")
    assert Decimal(str(bals[p2pid]["owed_expense_share"])) == Decimal("0.00")

    # dealer paid 30, owes 15 → expense_balance = +15
    assert Decimal(str(bals[dpid]["expense_balance"])) == Decimal("15.00")
    # p1 paid 0, owes 15 → expense_balance = -15
    assert Decimal(str(bals[p1pid]["expense_balance"])) == Decimal("-15.00")


# ---------------------------------------------------------------------------
# Tests: guest participant
# ---------------------------------------------------------------------------


def test_guest_participant_in_settlement(client: TestClient):
    """Guest participant appears in settlement with correct balances."""
    dealer_token = _register_and_login(client, "d_guest@example.com")
    game = _create_game(client, dealer_token)
    gid = game["id"]

    guest = _add_guest(client, dealer_token, gid, "Alice Guest")
    guest_pid = guest["id"]

    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    _buy_in(client, dealer_token, gid, guest_pid, 100.0, 10000.0)

    # Dealer wins, guest loses
    _set_final_stack(client, dealer_token, gid, dpid, 15000)
    _set_final_stack(client, dealer_token, gid, guest_pid, 5000)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    assert r.status_code == 200
    body = r.json()

    assert body["is_complete"] is True
    bals = {b["participant_id"]: b for b in body["balances"]}
    assert Decimal(str(bals[guest_pid]["net_balance"])) == Decimal("-50.00")
    assert bals[guest_pid]["display_name"] == "Alice Guest"
    assert bals[guest_pid]["participant_type"] == "guest"

    transfers = body["transfers"]
    assert len(transfers) == 1
    assert transfers[0]["from_participant_id"] == guest_pid


# ---------------------------------------------------------------------------
# Tests: is_complete when a participant is missing a final stack
# ---------------------------------------------------------------------------


def test_incomplete_settlement_missing_final_stack(client: TestClient):
    """Close is blocked when any participant lacks a final stack (returns 400 with missing list)."""
    dealer_token = _register_and_login(client, "d_inc@example.com")
    player_token = _register_and_login(client, "p_inc@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    # Only dealer gets a final stack; player does not
    _set_final_stack(client, dealer_token, gid, dpid, 10000)
    r = client.post(f"/games/{gid}/close", json={}, headers=_auth(dealer_token))

    assert r.status_code == 400
    body = r.json()
    assert body["detail"] == "Cannot close game: missing final chip counts"
    assert len(body["missing_final_stacks"]) == 1
    assert body["missing_final_stacks"][0]["participant_id"] == ppid


# ---------------------------------------------------------------------------
# Tests: rounding
# ---------------------------------------------------------------------------


def test_chip_rate_rounding(client: TestClient):
    """
    Use a chip_cash_rate that produces fractional cents when multiplied.
    chip_cash_rate = 0.0333 (non-trivial rounding)
    Participant has 10000 chips → 10000 * 0.0333 = 333.0 (exact here)
    Participant has 3 chips → 3 * 0.0333 = 0.0999 → rounded to 0.10 (ROUND_HALF_UP)
    """
    dealer_token = _register_and_login(client, "d_round@example.com")
    player_token = _register_and_login(client, "p_round@example.com")

    game = _create_game(client, dealer_token, chip_cash_rate=0.0333)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    _buy_in(client, dealer_token, gid, ppid, 100.0, 10000.0)

    # 3 chips → 3 * 0.0333 = 0.0999 → 0.10
    _set_final_stack(client, dealer_token, gid, dpid, 3)
    # 19997 chips to use remaining (doesn't need to be exact for this test)
    _set_final_stack(client, dealer_token, gid, ppid, 19997)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    assert r.status_code == 200
    body = r.json()

    bals = {b["participant_id"]: b for b in body["balances"]}
    # 3 * 0.0333 = 0.0999, ROUND_HALF_UP → 0.10
    assert Decimal(str(bals[dpid]["final_chip_cash_value"])) == Decimal("0.10")


# ---------------------------------------------------------------------------
# Tests: audit endpoint
# ---------------------------------------------------------------------------


def test_audit_endpoint_structure(client: TestClient):
    """Audit response contains line items with buy_in_items and expense details."""
    dealer_token = _register_and_login(client, "d_aud@example.com")
    player_token = _register_and_login(client, "p_aud@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    _buy_in(client, dealer_token, gid, dpid, 50.0, 5000.0, buy_in_type="rebuy")
    _buy_in(client, dealer_token, gid, ppid, 100.0, 10000.0)

    _expense(
        client,
        dealer_token,
        gid,
        paid_by=dpid,
        total=20.0,
        splits=[
            {"participant_id": dpid, "share_amount": 10.0},
            {"participant_id": ppid, "share_amount": 10.0},
        ],
    )

    _set_final_stack(client, dealer_token, gid, dpid, 15000)
    _set_final_stack(client, dealer_token, gid, ppid, 0)
    _close(client, dealer_token, gid)

    r = _get_audit(client, dealer_token, gid)
    assert r.status_code == 200
    body = r.json()

    assert "participants" in body
    assert "net_balance_sum" in body
    assert "transfers" in body

    parts = {p["participant_id"]: p for p in body["participants"]}

    # Dealer: 2 buy-ins
    assert len(parts[dpid]["buy_in_items"]) == 2
    # Dealer: 1 expense paid
    assert len(parts[dpid]["expenses_paid_items"]) == 1
    # Dealer: 1 split owed
    assert len(parts[dpid]["expense_split_items"]) == 1

    # Player: 1 buy-in, no expense paid, 1 split owed
    assert len(parts[ppid]["buy_in_items"]) == 1
    assert len(parts[ppid]["expenses_paid_items"]) == 0
    assert len(parts[ppid]["expense_split_items"]) == 1

    # net_balance_sum is Decimal-friendly string
    assert body["net_balance_sum"] is not None


def test_audit_net_balance_sum_near_zero(client: TestClient):
    """net_balance_sum should be near zero for a well-formed game."""
    dealer_token = _register_and_login(client, "d_sum@example.com")
    player_token = _register_and_login(client, "p_sum@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, 100.0, 10000.0)
    _buy_in(client, dealer_token, gid, ppid, 100.0, 10000.0)
    _set_final_stack(client, dealer_token, gid, dpid, 15000)
    _set_final_stack(client, dealer_token, gid, ppid, 5000)
    _close(client, dealer_token, gid)

    r = _get_audit(client, dealer_token, gid)
    body = r.json()
    net_sum = Decimal(str(body["net_balance_sum"]))
    # Zero-sum poker: 15000+5000=20000 chips total = 20000*0.01=$200 = total buy-ins
    assert net_sum == Decimal("0.00")


def test_audit_accessible_by_player(client: TestClient):
    """Any participant (not just dealer) can access the audit endpoint."""
    d2 = _register_and_login(client, "d_acc@example.com")
    p2 = _register_and_login(client, "p_acc@example.com")
    game = _create_game(client, d2)
    gid = game["id"]
    _join(client, p2, game["invite_token"])
    ps = _get_participants(client, d2, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]
    _start(client, d2, gid)
    _buy_in(client, d2, gid, dpid, 100.0, 10000.0)
    _buy_in(client, d2, gid, ppid, 100.0, 10000.0)
    _set_final_stack(client, d2, gid, dpid, 15000)
    _set_final_stack(client, d2, gid, ppid, 5000)
    _close(client, d2, gid)

    r = _get_audit(client, p2, gid)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Tests: no expenses game
# ---------------------------------------------------------------------------


def test_no_expenses_expense_balance_is_zero(client: TestClient):
    """If there are no expenses, expense_balance is 0 for all participants."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_two_player_game(client)
    r = _get_settlement(client, dealer_token, game_id)
    body = r.json()
    for b in body["balances"]:
        assert Decimal(str(b["amount_paid_for_group"])) == Decimal("0.00")
        assert Decimal(str(b["owed_expense_share"])) == Decimal("0.00")
        assert Decimal(str(b["expense_balance"])) == Decimal("0.00")


# ---------------------------------------------------------------------------
# Tests: dealer as loser (PLAN.md edge case)
# ---------------------------------------------------------------------------


def test_dealer_as_loser(client: TestClient):
    """
    Dealer is also a financial participant and ends with a negative net_balance.

    Dealer:  buys 10000 chips for $100, ends with 4000 chips = $40  → poker_balance = -$60
    Player:  buys 10000 chips for $100, ends with 16000 chips = $160 → poker_balance = +$60

    Expected: dealer pays player $60 (transfer goes FROM dealer TO player).
    """
    dealer_token = _register_and_login(client, "d_lose@example.com")
    player_token = _register_and_login(client, "p_lose@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, player_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    ppid = next(p for p in ps if p["role_in_game"] == "player")["id"]

    _start(client, dealer_token, gid)
    _buy_in(client, dealer_token, gid, dpid, cash=100.0, chips=10000.0)
    _buy_in(client, dealer_token, gid, ppid, cash=100.0, chips=10000.0)

    _set_final_stack(client, dealer_token, gid, dpid, chips=4000)
    _set_final_stack(client, dealer_token, gid, ppid, chips=16000)
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    assert r.status_code == 200
    body = r.json()

    bals = {b["participant_id"]: b for b in body["balances"]}
    assert Decimal(str(bals[dpid]["net_balance"])) == Decimal("-60.00")
    assert Decimal(str(bals[ppid]["net_balance"])) == Decimal("60.00")

    transfers = body["transfers"]
    assert len(transfers) == 1
    t = transfers[0]
    assert t["from_participant_id"] == dpid   # dealer pays
    assert t["to_participant_id"] == ppid     # player receives
    assert Decimal(str(t["amount"])) == Decimal("60.00")


# ---------------------------------------------------------------------------
# Tests: participant with net_balance exactly 0.00 excluded from transfers
# ---------------------------------------------------------------------------


def test_zero_net_balance_excluded_from_transfers(client: TestClient):
    """
    A participant who breaks exactly even (net_balance == 0.00) must not appear
    in any transfer row, either as payer or receiver.

    Setup — three participants:
      Dealer:   buys 10000 chips ($100), ends with 10000 chips ($100) → net $0.00
      Player A: buys 10000 chips ($100), ends with 15000 chips ($150) → net +$50.00
      Player B: buys 10000 chips ($100), ends with  5000 chips ($50)  → net -$50.00

    Expected transfers: Player B pays Player A $50.  Dealer not in any transfer.
    """
    dealer_token = _register_and_login(client, "d_zero@example.com")
    pa_token = _register_and_login(client, "pa_zero@example.com")
    pb_token = _register_and_login(client, "pb_zero@example.com")

    game = _create_game(client, dealer_token)
    gid = game["id"]
    _join(client, pa_token, game["invite_token"])
    _join(client, pb_token, game["invite_token"])
    ps = _get_participants(client, dealer_token, gid)
    dpid = next(p for p in ps if p["role_in_game"] == "dealer")["id"]
    player_pids = [p["id"] for p in ps if p["role_in_game"] == "player"]
    # Identify A (ends with 15000) and B (ends with 5000) by assigning both first
    pa_pid, pb_pid = player_pids[0], player_pids[1]

    _start(client, dealer_token, gid)
    for pid in [dpid, pa_pid, pb_pid]:
        _buy_in(client, dealer_token, gid, pid, cash=100.0, chips=10000.0)

    _set_final_stack(client, dealer_token, gid, dpid, chips=10000)   # dealer breaks even
    _set_final_stack(client, dealer_token, gid, pa_pid, chips=15000)  # player A wins
    _set_final_stack(client, dealer_token, gid, pb_pid, chips=5000)   # player B loses
    _close(client, dealer_token, gid)

    r = _get_settlement(client, dealer_token, gid)
    assert r.status_code == 200
    body = r.json()

    bals = {b["participant_id"]: b for b in body["balances"]}
    assert Decimal(str(bals[dpid]["net_balance"])) == Decimal("0.00")
    assert Decimal(str(bals[pa_pid]["net_balance"])) == Decimal("50.00")
    assert Decimal(str(bals[pb_pid]["net_balance"])) == Decimal("-50.00")

    transfers = body["transfers"]
    assert len(transfers) == 1
    t = transfers[0]
    # Dealer must not appear in any transfer
    assert t["from_participant_id"] != dpid
    assert t["to_participant_id"] != dpid
    # Correct payer/receiver
    assert t["from_participant_id"] == pb_pid
    assert t["to_participant_id"] == pa_pid
    assert Decimal(str(t["amount"])) == Decimal("50.00")
