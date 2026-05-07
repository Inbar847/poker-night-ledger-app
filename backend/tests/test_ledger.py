"""
Tests for Stage 3: buy-ins, expenses, final stacks, and game status transitions.

Test helper pattern:
- _setup_active_game() creates a game, starts it, and returns the dealer token,
  player token, dealer participant id, and player participant id needed by most tests.
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared helpers
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


def _create_game(client: TestClient, token: str) -> dict:
    return client.post("/games", json=_GAME_PAYLOAD, headers=_auth(token)).json()


def _start_game(client: TestClient, token: str, game_id: str) -> dict:
    return client.post(f"/games/{game_id}/start", headers=_auth(token))


def _setup_lobby_game(client: TestClient) -> tuple[str, str, str, str, str]:
    """Returns (dealer_token, player_token, game_id, dealer_participant_id, player_participant_id)."""
    dealer_token = _register_and_login(client, "dealer@example.com")
    player_token = _register_and_login(client, "player@example.com")

    game = _create_game(client, dealer_token)
    game_id = game["id"]

    # Player joins
    client.post(
        "/games/join-by-token",
        json={"token": game["invite_token"]},
        headers=_auth(player_token),
    )

    # Get participant IDs
    participants = client.get(
        f"/games/{game_id}/participants", headers=_auth(dealer_token)
    ).json()
    dealer_part = next(p for p in participants if p["role_in_game"] == "dealer")
    player_part = next(p for p in participants if p["role_in_game"] == "player")

    return dealer_token, player_token, game_id, dealer_part["id"], player_part["id"]


def _setup_active_game(client: TestClient) -> tuple[str, str, str, str, str]:
    """Like _setup_lobby_game but also starts the game."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_lobby_game(client)
    _start_game(client, dealer_token, game_id)
    return dealer_token, player_token, game_id, dealer_pid, player_pid


# ---------------------------------------------------------------------------
# Game status transitions: start
# ---------------------------------------------------------------------------


def test_start_game_success(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, dealer_token)
    resp = _start_game(client, dealer_token, game["id"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_start_game_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, *_ = _setup_lobby_game(client)
    resp = _start_game(client, player_token, game_id)
    assert resp.status_code == 403


def test_start_game_requires_auth(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, dealer_token)
    resp = client.post(f"/games/{game['id']}/start")
    assert resp.status_code == 401


def test_start_game_already_active_returns_400(client: TestClient):
    dealer_token, _, game_id, *_ = _setup_active_game(client)
    resp = _start_game(client, dealer_token, game_id)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Game status transitions: close
# ---------------------------------------------------------------------------


def test_close_game_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # All participants need final stacks before close (0 chips = no shortage)
    client.put(f"/games/{game_id}/final-stacks/{dealer_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    client.put(f"/games/{game_id}/final-stacks/{player_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    resp = client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "closed"
    assert body["closed_at"] is not None


def test_close_game_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, *_ = _setup_active_game(client)
    resp = client.post(f"/games/{game_id}/close", headers=_auth(player_token))
    assert resp.status_code == 403


def test_close_lobby_game_returns_400(client: TestClient):
    dealer_token = _register_and_login(client, "dealer@example.com")
    game = _create_game(client, dealer_token)
    resp = client.post(f"/games/{game['id']}/close", headers=_auth(dealer_token))
    assert resp.status_code == 400


def test_close_already_closed_game_returns_400(client: TestClient):
    dealer_token, _, game_id, *_ = _setup_active_game(client)
    client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    resp = client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Buy-ins: create
# ---------------------------------------------------------------------------


def _buy_in_payload(participant_id: str, cash: float = 50.0, chips: float = 5000.0) -> dict:
    return {
        "participant_id": participant_id,
        "cash_amount": cash,
        "chips_amount": chips,
        "buy_in_type": "initial",
    }


def test_create_buy_in_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["cash_amount"] == "50.00"
    assert body["chips_amount"] == "5000.00"
    assert body["buy_in_type"] == "initial"
    assert body["game_id"] == game_id
    assert body["participant_id"] == dealer_pid


def test_create_buy_in_for_player(client: TestClient):
    dealer_token, _, game_id, _, player_pid = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(player_pid),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 201


def test_create_multiple_buy_ins_same_participant(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid, cash=50.0),
        headers=_auth(dealer_token),
    )
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid, cash=25.0, chips=2500.0) | {"buy_in_type": "rebuy"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 201
    assert resp.json()["buy_in_type"] == "rebuy"


def test_create_buy_in_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, _, player_pid = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(player_pid),
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


def test_create_buy_in_requires_auth(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.post(f"/games/{game_id}/buy-ins", json=_buy_in_payload(dealer_pid))
    assert resp.status_code == 401


def test_create_buy_in_on_lobby_game_returns_400(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_lobby_game(client)
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_create_buy_in_on_closed_game_returns_400(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.put(f"/games/{game_id}/final-stacks/{dealer_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    client.put(f"/games/{game_id}/final-stacks/{player_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_create_buy_in_participant_not_in_game_returns_400(client: TestClient):
    dealer_token, _, game_id, _, _ = _setup_active_game(client)
    fake_id = "00000000-0000-0000-0000-000000000099"
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(fake_id),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_create_buy_in_zero_cash_invalid(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid, cash=0),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Buy-ins: list
# ---------------------------------------------------------------------------


def test_list_buy_ins_returns_all(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(player_pid),
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/buy-ins", headers=_auth(dealer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_buy_ins_accessible_by_player(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, _ = _setup_active_game(client)
    client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/buy-ins", headers=_auth(player_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_buy_ins_forbidden_for_non_participant(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    outsider_token = _register_and_login(client, "outsider@example.com")
    client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/buy-ins", headers=_auth(outsider_token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Buy-ins: update
# ---------------------------------------------------------------------------


def test_update_buy_in_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    buy_in = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/buy-ins/{buy_in['id']}",
        json={"cash_amount": 100.0, "buy_in_type": "rebuy"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["cash_amount"] == "100.00"
    assert body["buy_in_type"] == "rebuy"
    assert body["chips_amount"] == "5000.00"  # unchanged


def test_update_buy_in_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, _ = _setup_active_game(client)
    buy_in = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/buy-ins/{buy_in['id']}",
        json={"cash_amount": 100.0},
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


def test_update_buy_in_not_found(client: TestClient):
    dealer_token, _, game_id, *_ = _setup_active_game(client)
    fake_id = "00000000-0000-0000-0000-000000000099"
    resp = client.patch(
        f"/games/{game_id}/buy-ins/{fake_id}",
        json={"cash_amount": 100.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Buy-ins: delete
# ---------------------------------------------------------------------------


def test_delete_buy_in_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    buy_in = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/buy-ins/{buy_in['id']}", headers=_auth(dealer_token)
    )
    assert resp.status_code == 204
    remaining = client.get(f"/games/{game_id}/buy-ins", headers=_auth(dealer_token)).json()
    assert len(remaining) == 0


def test_delete_buy_in_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, _ = _setup_active_game(client)
    buy_in = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/buy-ins/{buy_in['id']}", headers=_auth(player_token)
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Expenses: create
# ---------------------------------------------------------------------------


def _expense_payload(paid_by: str, participant_ids: list[str]) -> dict:
    share = round(60.0 / len(participant_ids), 2)
    splits = [{"participant_id": pid, "share_amount": share} for pid in participant_ids]
    # Adjust last split for rounding
    total = round(share * len(participant_ids), 2)
    if total != 60.0:
        splits[-1]["share_amount"] = round(60.0 - share * (len(participant_ids) - 1), 2)
    return {
        "title": "Pizza",
        "total_amount": 60.0,
        "paid_by_participant_id": paid_by,
        "splits": splits,
    }


def test_create_expense_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Pizza"
    assert body["total_amount"] == "60.00"
    assert body["paid_by_participant_id"] == dealer_pid
    assert len(body["splits"]) == 2


def test_create_expense_splits_must_sum_to_total(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    bad_payload = {
        "title": "Beer",
        "total_amount": 30.0,
        "paid_by_participant_id": dealer_pid,
        "splits": [
            {"participant_id": dealer_pid, "share_amount": 10.0},
            {"participant_id": player_pid, "share_amount": 5.0},  # 15.0 != 30.0
        ],
    }
    resp = client.post(
        f"/games/{game_id}/expenses", json=bad_payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 422


def test_create_expense_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    resp = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


def test_create_expense_on_lobby_game_returns_400(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_lobby_game(client)
    resp = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_create_expense_participant_not_in_game(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    fake_id = "00000000-0000-0000-0000-000000000099"
    bad_payload = {
        "title": "Beer",
        "total_amount": 20.0,
        "paid_by_participant_id": dealer_pid,
        "splits": [{"participant_id": fake_id, "share_amount": 20.0}],
    }
    resp = client.post(
        f"/games/{game_id}/expenses", json=bad_payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 400


def test_create_expense_split_across_subset(client: TestClient):
    """Expense can be split across fewer participants than are in the game."""
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    payload = {
        "title": "Dealer snack",
        "total_amount": 10.0,
        "paid_by_participant_id": dealer_pid,
        "splits": [{"participant_id": dealer_pid, "share_amount": 10.0}],
    }
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 201
    assert len(resp.json()["splits"]) == 1


# ---------------------------------------------------------------------------
# Expenses: list
# ---------------------------------------------------------------------------


def test_list_expenses_returns_all(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    )
    client.post(
        f"/games/{game_id}/expenses",
        json={**_expense_payload(dealer_pid, [dealer_pid]), "title": "Beer"},
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/expenses", headers=_auth(dealer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_expenses_accessible_by_player(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/expenses", headers=_auth(player_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# Expenses: update
# ---------------------------------------------------------------------------


def test_update_expense_title(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "Sushi"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Sushi"


def test_update_expense_with_new_splits(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    # Update: only dealer pays now, only dealer is in the split
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={
            "total_amount": 40.0,
            "splits": [{"participant_id": dealer_pid, "share_amount": 40.0}],
        },
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_amount"] == "40.00"
    assert len(body["splits"]) == 1
    assert body["splits"][0]["share_amount"] == "40.00"


def test_update_expense_splits_only_no_total_amount(client: TestClient):
    """PATCH with new splits but no total_amount — service must validate splits against
    the existing DB total_amount, not the (absent) request total_amount."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # Original expense: 60.00 split evenly between two participants
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    assert expense["total_amount"] == "60.00"
    assert len(expense["splits"]) == 2

    # PATCH: new splits that still sum to 60.00 (dealer pays 40, player pays 20)
    # total_amount is intentionally omitted
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={
            "splits": [
                {"participant_id": dealer_pid, "share_amount": 40.0},
                {"participant_id": player_pid, "share_amount": 20.0},
            ]
        },
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_amount"] == "60.00"  # unchanged
    assert len(body["splits"]) == 2
    shares = {s["participant_id"]: s["share_amount"] for s in body["splits"]}
    assert shares[dealer_pid] == "40.00"
    assert shares[player_pid] == "20.00"


def test_update_expense_splits_only_wrong_sum_returns_400(client: TestClient):
    """PATCH with splits that don't sum to the existing total_amount must be rejected."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()

    # Splits sum to 50.00 but total_amount in DB is 60.00
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={
            "splits": [
                {"participant_id": dealer_pid, "share_amount": 30.0},
                {"participant_id": player_pid, "share_amount": 20.0},
            ]
        },
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_create_expense_duplicate_participant_in_splits_rejected(client: TestClient):
    """Splits list with the same participant_id appearing twice must be rejected."""
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    bad_payload = {
        "title": "Pizza",
        "total_amount": 60.0,
        "paid_by_participant_id": dealer_pid,
        "splits": [
            {"participant_id": dealer_pid, "share_amount": 30.0},
            {"participant_id": dealer_pid, "share_amount": 30.0},  # duplicate
        ],
    }
    resp = client.post(
        f"/games/{game_id}/expenses", json=bad_payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 400


def test_update_expense_duplicate_participant_in_splits_rejected(client: TestClient):
    """PATCH with duplicate participant_id in new splits must be rejected."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={
            "splits": [
                {"participant_id": dealer_pid, "share_amount": 30.0},
                {"participant_id": dealer_pid, "share_amount": 30.0},  # duplicate
            ]
        },
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_expense_split_unique_constraint_at_db_level(client: TestClient, db_session):
    """The DB itself must reject duplicate (expense_id, participant_id) rows,
    even if application validation is somehow bypassed."""
    from app.models.ledger import ExpenseSplit
    from sqlalchemy.exc import IntegrityError
    import uuid

    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()

    expense_id = uuid.UUID(expense["id"])
    participant_id = uuid.UUID(dealer_pid)

    # Try to insert a duplicate split directly at the DB level
    duplicate = ExpenseSplit(
        expense_id=expense_id,
        participant_id=participant_id,
        share_amount=10.00,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_update_expense_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "Hacked"},
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Expenses: delete
# ---------------------------------------------------------------------------


def test_delete_expense_success(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/expenses/{expense['id']}", headers=_auth(dealer_token)
    )
    assert resp.status_code == 204
    remaining = client.get(f"/games/{game_id}/expenses", headers=_auth(dealer_token)).json()
    assert len(remaining) == 0


def test_delete_expense_dealer_only(client: TestClient):
    """Non-creator non-dealer cannot delete an expense created by the dealer."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/expenses/{expense['id']}", headers=_auth(player_token)
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Expenses: player-added side expenses (Stage 27)
# ---------------------------------------------------------------------------


def test_player_creates_expense_self_as_payer(client: TestClient):
    """Non-dealer active participant creates expense with self as payer — allowed."""
    _, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    payload = _expense_payload(player_pid, [dealer_pid, player_pid])
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(player_token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["paid_by_participant_id"] == player_pid


def test_player_creates_expense_different_payer_blocked(client: TestClient):
    """Non-dealer cannot create expense claiming someone else paid."""
    _, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    payload = _expense_payload(dealer_pid, [dealer_pid, player_pid])
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(player_token)
    )
    assert resp.status_code == 403


def test_dealer_creates_expense_any_payer(client: TestClient):
    """Dealer can create expense with any participant as payer."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # Dealer sets player as payer (not themselves)
    payload = _expense_payload(player_pid, [dealer_pid, player_pid])
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 201
    assert resp.json()["paid_by_participant_id"] == player_pid


def test_left_early_participant_cannot_create_expense(client: TestClient):
    """Participant who has cashed out (left_early) cannot create expenses."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # Player cashes out
    client.post(
        f"/games/{game_id}/cashout",
        json={"chips_amount": "1000"},
        headers=_auth(player_token),
    )
    # Player tries to create expense after leaving
    payload = _expense_payload(player_pid, [dealer_pid, player_pid])
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(player_token)
    )
    assert resp.status_code == 403


def test_creator_edits_own_expense(client: TestClient):
    """The expense creator (non-dealer) can edit their own expense."""
    _, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(player_pid, [dealer_pid, player_pid]),
        headers=_auth(player_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "Updated by creator"},
        headers=_auth(player_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated by creator"


def test_creator_deletes_own_expense(client: TestClient):
    """The expense creator (non-dealer) can delete their own expense."""
    _, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(player_pid, [dealer_pid, player_pid]),
        headers=_auth(player_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/expenses/{expense['id']}", headers=_auth(player_token)
    )
    assert resp.status_code == 204


def test_non_creator_non_dealer_cannot_edit_expense(client: TestClient):
    """A participant who is neither creator nor dealer cannot edit an expense."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # Dealer creates the expense
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    # Player (non-creator, non-dealer) tries to edit
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "Hacked"},
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


def test_non_creator_non_dealer_cannot_delete_expense(client: TestClient):
    """A participant who is neither creator nor dealer cannot delete an expense."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/expenses/{expense['id']}", headers=_auth(player_token)
    )
    assert resp.status_code == 403


def test_dealer_edits_any_expense(client: TestClient):
    """Dealer can edit an expense created by another participant."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    # Player creates expense
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(player_pid, [dealer_pid, player_pid]),
        headers=_auth(player_token),
    ).json()
    # Dealer edits it
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "Dealer override"},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Dealer override"


def test_dealer_deletes_any_expense(client: TestClient):
    """Dealer can delete an expense created by another participant."""
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(player_pid, [dealer_pid, player_pid]),
        headers=_auth(player_token),
    ).json()
    resp = client.delete(
        f"/games/{game_id}/expenses/{expense['id']}", headers=_auth(dealer_token)
    )
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Final stacks: upsert
# ---------------------------------------------------------------------------


def test_upsert_final_stack_create(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["chips_amount"] == "8000.00"
    assert body["participant_id"] == dealer_pid
    assert body["game_id"] == game_id


def test_upsert_final_stack_update(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 9500.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200
    assert resp.json()["chips_amount"] == "9500.00"


def test_upsert_final_stack_one_row_per_participant(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 1000.0},
        headers=_auth(dealer_token),
    )
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 2000.0},
        headers=_auth(dealer_token),
    )
    stacks = client.get(f"/games/{game_id}/final-stacks", headers=_auth(dealer_token)).json()
    assert len(stacks) == 1
    assert stacks[0]["chips_amount"] == "2000.00"


def test_upsert_final_stack_zero_chips_allowed(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 200


def test_upsert_final_stack_dealer_only(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, _ = _setup_active_game(client)
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(player_token),
    )
    assert resp.status_code == 403


def test_upsert_final_stack_on_lobby_game_returns_400(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_lobby_game(client)
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_upsert_final_stack_on_closed_game_returns_400(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.put(f"/games/{game_id}/final-stacks/{dealer_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    client.put(f"/games/{game_id}/final-stacks/{player_pid}", json={"chips_amount": 0.0}, headers=_auth(dealer_token))
    client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    resp = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


def test_upsert_final_stack_participant_not_in_game(client: TestClient):
    dealer_token, _, game_id, *_ = _setup_active_game(client)
    fake_id = "00000000-0000-0000-0000-000000000099"
    resp = client.put(
        f"/games/{game_id}/final-stacks/{fake_id}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Final stacks: list
# ---------------------------------------------------------------------------


def test_list_final_stacks_returns_all(client: TestClient):
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    client.put(
        f"/games/{game_id}/final-stacks/{player_pid}",
        json={"chips_amount": 2000.0},
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/final-stacks", headers=_auth(dealer_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_final_stacks_accessible_by_player(client: TestClient):
    dealer_token, player_token, game_id, dealer_pid, _ = _setup_active_game(client)
    client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 8000.0},
        headers=_auth(dealer_token),
    )
    resp = client.get(f"/games/{game_id}/final-stacks", headers=_auth(player_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_final_stacks_forbidden_for_non_participant(client: TestClient):
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    outsider_token = _register_and_login(client, "outsider@example.com")
    resp = client.get(f"/games/{game_id}/final-stacks", headers=_auth(outsider_token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Full ledger flow integration test
# ---------------------------------------------------------------------------


def test_full_game_ledger_flow(client: TestClient):
    """
    Simulates a complete game: lobby → active → buy-ins → expenses →
    final stacks → closed.
    """
    dealer_token, player_token, game_id, dealer_pid, player_pid = _setup_active_game(client)

    # Dealer buys in
    r1 = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": dealer_pid, "cash_amount": 100.0, "chips_amount": 10000.0, "buy_in_type": "initial"},
        headers=_auth(dealer_token),
    )
    assert r1.status_code == 201

    # Player buys in
    r2 = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": player_pid, "cash_amount": 50.0, "chips_amount": 5000.0, "buy_in_type": "initial"},
        headers=_auth(dealer_token),
    )
    assert r2.status_code == 201

    # Player rebuys
    r3 = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": player_pid, "cash_amount": 50.0, "chips_amount": 5000.0, "buy_in_type": "rebuy"},
        headers=_auth(dealer_token),
    )
    assert r3.status_code == 201

    # Add expense: pizza, split evenly
    r4 = client.post(
        f"/games/{game_id}/expenses",
        json={
            "title": "Pizza",
            "total_amount": 40.0,
            "paid_by_participant_id": dealer_pid,
            "splits": [
                {"participant_id": dealer_pid, "share_amount": 20.0},
                {"participant_id": player_pid, "share_amount": 20.0},
            ],
        },
        headers=_auth(dealer_token),
    )
    assert r4.status_code == 201

    # Set final stacks
    r5 = client.put(
        f"/games/{game_id}/final-stacks/{dealer_pid}",
        json={"chips_amount": 14000.0},
        headers=_auth(dealer_token),
    )
    assert r5.status_code == 200

    r6 = client.put(
        f"/games/{game_id}/final-stacks/{player_pid}",
        json={"chips_amount": 6000.0},
        headers=_auth(dealer_token),
    )
    assert r6.status_code == 200

    # Close the game
    close_resp = client.post(f"/games/{game_id}/close", headers=_auth(dealer_token))
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    # Verify all ledger data is still readable after close
    buy_ins = client.get(f"/games/{game_id}/buy-ins", headers=_auth(dealer_token)).json()
    assert len(buy_ins) == 3

    expenses = client.get(f"/games/{game_id}/expenses", headers=_auth(dealer_token)).json()
    assert len(expenses) == 1

    stacks = client.get(f"/games/{game_id}/final-stacks", headers=_auth(dealer_token)).json()
    assert len(stacks) == 2

    # Mutations must fail on closed game
    r_fail = client.post(
        f"/games/{game_id}/buy-ins",
        json={"participant_id": dealer_pid, "cash_amount": 10.0, "chips_amount": 1000.0, "buy_in_type": "addon"},
        headers=_auth(dealer_token),
    )
    assert r_fail.status_code == 400


# ---------------------------------------------------------------------------
# Stage 9: validation edge cases
# ---------------------------------------------------------------------------


def test_update_buy_in_all_none_fields_returns_422(client: TestClient):
    """PATCH buy-in with no fields set must be rejected at schema level."""
    dealer_token, _, game_id, dealer_pid, _ = _setup_active_game(client)
    buy_in = client.post(
        f"/games/{game_id}/buy-ins",
        json=_buy_in_payload(dealer_pid),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/buy-ins/{buy_in['id']}",
        json={},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 422


def test_create_expense_whitespace_only_title_returns_422(client: TestClient):
    """Expense title consisting only of whitespace must be rejected."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    payload = {
        "title": "   ",
        "total_amount": 20.0,
        "paid_by_participant_id": dealer_pid,
        "splits": [{"participant_id": dealer_pid, "share_amount": 20.0}],
    }
    resp = client.post(
        f"/games/{game_id}/expenses", json=payload, headers=_auth(dealer_token)
    )
    assert resp.status_code == 422


def test_update_expense_whitespace_only_title_returns_422(client: TestClient):
    """PATCH expense title to whitespace-only must be rejected."""
    dealer_token, _, game_id, dealer_pid, player_pid = _setup_active_game(client)
    expense = client.post(
        f"/games/{game_id}/expenses",
        json=_expense_payload(dealer_pid, [dealer_pid, player_pid]),
        headers=_auth(dealer_token),
    ).json()
    resp = client.patch(
        f"/games/{game_id}/expenses/{expense['id']}",
        json={"title": "   "},
        headers=_auth(dealer_token),
    )
    assert resp.status_code == 422
