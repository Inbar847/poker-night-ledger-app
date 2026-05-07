"""
Tests for participant lifecycle statuses (Stage 20).

Covers:
- New participants default to 'active' status
- ParticipantResponse includes status field
- set_participant_status transitions work correctly
- get_settlement_eligible_participants returns active + left_early, excludes removed_before_start
- Close-game validation excludes removed_before_start from final-stack requirement
- Settlement excludes removed_before_start participants
- left_early participants are included in settlement normally
"""

import uuid as uuid_mod

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.participant import Participant, ParticipantStatus


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
        json={"title": "Status Game", "chip_cash_rate": "0.10", "currency": "USD"},
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


def _close(client: TestClient, token: str, game_id: str):
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


def _get_settlement(client: TestClient, token: str, game_id: str) -> dict:
    r = client.get(f"/games/{game_id}/settlement", headers=_auth(token))
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Tests — Default status
# ---------------------------------------------------------------------------


class TestParticipantStatusDefaults:
    def test_new_participant_has_active_status(self, client: TestClient):
        """Newly created participants default to 'active' status."""
        token, _ = _register_and_login(client, "ps_default@test.com")
        game = _create_game(client, token)
        parts = _get_participants(client, token, game["id"])
        assert len(parts) == 1
        assert parts[0]["status"] == "active"

    def test_guest_has_active_status(self, client: TestClient):
        """Guest participants also default to 'active' status."""
        token, _ = _register_and_login(client, "ps_guest@test.com")
        game = _create_game(client, token)
        guest = _add_guest(client, token, game["id"], "Guest 1")
        assert guest["status"] == "active"

    def test_joined_player_has_active_status(self, client: TestClient):
        """A player joining via invite token has 'active' status."""
        dealer_token, _ = _register_and_login(client, "ps_join_d@test.com")
        player_token, _ = _register_and_login(client, "ps_join_p@test.com")
        game = _create_game(client, dealer_token)
        invite_tok = _invite_link(client, dealer_token, game["id"])
        joined = _join_by_token(client, player_token, invite_tok)
        assert joined["status"] == "active"


# ---------------------------------------------------------------------------
# Tests — Status transitions (service level, via DB)
# ---------------------------------------------------------------------------


class TestParticipantStatusTransitions:
    def test_set_participant_status_left_early(self, client: TestClient, db_session: Session):
        """set_participant_status can change a participant to left_early."""
        from app.services import participant_service

        token, _ = _register_and_login(client, "ps_trans_le@test.com")
        game = _create_game(client, token)
        parts = _get_participants(client, token, game["id"])
        pid = uuid_mod.UUID(parts[0]["id"])

        participant = db_session.get(Participant, pid)
        assert participant.status == ParticipantStatus.active

        participant_service.set_participant_status(db_session, pid, ParticipantStatus.left_early)
        db_session.expire_all()
        participant = db_session.get(Participant, pid)
        assert participant.status == ParticipantStatus.left_early

    def test_set_participant_status_removed_before_start(self, client: TestClient, db_session: Session):
        """set_participant_status can change a participant to removed_before_start."""
        from app.services import participant_service

        token, _ = _register_and_login(client, "ps_trans_rbs@test.com")
        game = _create_game(client, token)
        guest = _add_guest(client, token, game["id"], "To Remove")
        pid = uuid_mod.UUID(guest["id"])

        participant_service.set_participant_status(
            db_session, pid, ParticipantStatus.removed_before_start
        )
        db_session.expire_all()
        participant = db_session.get(Participant, pid)
        assert participant.status == ParticipantStatus.removed_before_start

    def test_set_status_nonexistent_raises(self, db_session: Session):
        """set_participant_status raises ValueError for unknown participant."""
        from app.services import participant_service

        import pytest
        with pytest.raises(ValueError, match="not found"):
            participant_service.set_participant_status(
                db_session, uuid_mod.uuid4(), ParticipantStatus.left_early
            )


# ---------------------------------------------------------------------------
# Tests — Settlement eligibility
# ---------------------------------------------------------------------------


class TestSettlementEligibility:
    def test_get_settlement_eligible_excludes_removed(self, client: TestClient, db_session: Session):
        """get_settlement_eligible_participants excludes removed_before_start."""
        from app.services import participant_service

        token, _ = _register_and_login(client, "ps_elig_d@test.com")
        game = _create_game(client, token)
        guest = _add_guest(client, token, game["id"], "Removed Guest")

        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest["id"]), ParticipantStatus.removed_before_start
        )
        db_session.expire_all()

        eligible = participant_service.get_settlement_eligible_participants(
            db_session, uuid_mod.UUID(game["id"])
        )
        eligible_ids = [str(p.id) for p in eligible]
        # Dealer is eligible, removed guest is not
        parts = _get_participants(client, token, game["id"])
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        assert dealer_pid in eligible_ids
        assert guest["id"] not in eligible_ids

    def test_left_early_is_eligible(self, client: TestClient, db_session: Session):
        """left_early participants are included in settlement eligibility."""
        from app.services import participant_service

        token, _ = _register_and_login(client, "ps_elig_le@test.com")
        game = _create_game(client, token)
        guest = _add_guest(client, token, game["id"], "Early Leaver")

        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest["id"]), ParticipantStatus.left_early
        )
        db_session.expire_all()

        eligible = participant_service.get_settlement_eligible_participants(
            db_session, uuid_mod.UUID(game["id"])
        )
        eligible_ids = [str(p.id) for p in eligible]
        assert guest["id"] in eligible_ids


# ---------------------------------------------------------------------------
# Tests — Close-game validation with statuses
# ---------------------------------------------------------------------------


class TestCloseGameWithStatuses:
    def test_removed_before_start_not_required_for_close(self, client: TestClient, db_session: Session):
        """A removed_before_start participant does not block game close."""
        from app.services import participant_service

        dealer_token, _ = _register_and_login(client, "ps_close_d@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        guest = _add_guest(client, dealer_token, gid, "Removed Before Start")

        # Remove the guest before start
        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest["id"]), ParticipantStatus.removed_before_start
        )
        db_session.commit()

        _start(client, dealer_token, gid)

        # Add buy-in and final stack for dealer only
        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1000")

        # Close should succeed — removed guest doesn't need a final stack
        r = _close(client, dealer_token, gid)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "closed"

    def test_left_early_with_stack_does_not_block_close(self, client: TestClient, db_session: Session):
        """A left_early participant with a final stack does not block close."""
        from app.services import participant_service

        dealer_token, _ = _register_and_login(client, "ps_close_le_d@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        guest = _add_guest(client, dealer_token, gid, "Early Leaver")

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        guest_pid = guest["id"]

        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        _add_buy_in(client, dealer_token, gid, guest_pid, "50.00", "500")
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")
        _set_final_stack(client, dealer_token, gid, guest_pid, "300")

        # Mark guest as left_early (they already have a final stack)
        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest_pid), ParticipantStatus.left_early
        )
        db_session.commit()

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "closed"

    def test_left_early_without_stack_blocks_close(self, client: TestClient, db_session: Session):
        """A left_early participant without a final stack blocks close."""
        from app.services import participant_service

        dealer_token, _ = _register_and_login(client, "ps_close_le_ns@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        guest = _add_guest(client, dealer_token, gid, "No Stack Leaver")

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1000")

        # Mark guest as left_early but don't set their final stack
        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest["id"]), ParticipantStatus.left_early
        )
        db_session.commit()

        r = _close(client, dealer_token, gid)
        assert r.status_code == 400
        body = r.json()
        assert "missing final chip counts" in body["detail"]
        missing_ids = [m["participant_id"] for m in body["missing_final_stacks"]]
        assert guest["id"] in missing_ids


# ---------------------------------------------------------------------------
# Tests — Settlement with statuses
# ---------------------------------------------------------------------------


class TestSettlementWithStatuses:
    def test_settlement_excludes_removed_before_start(self, client: TestClient, db_session: Session):
        """Settlement does not include removed_before_start participants."""
        from app.services import participant_service

        dealer_token, _ = _register_and_login(client, "ps_settle_d@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]
        guest = _add_guest(client, dealer_token, gid, "Removed Guest")

        # Remove guest before start
        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(guest["id"]), ParticipantStatus.removed_before_start
        )
        db_session.commit()

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")
        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1000")

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200, r.text

        settlement = _get_settlement(client, dealer_token, gid)
        balance_pids = [b["participant_id"] for b in settlement["balances"]]
        assert dealer_pid in balance_pids
        assert guest["id"] not in balance_pids

    def test_settlement_includes_left_early(self, client: TestClient, db_session: Session):
        """Settlement includes left_early participants normally."""
        from app.services import participant_service

        dealer_token, _ = _register_and_login(client, "ps_settle_le_d@test.com")
        player_token, _ = _register_and_login(client, "ps_settle_le_p@test.com")
        game = _create_game(client, dealer_token)
        gid = game["id"]

        invite_tok = _invite_link(client, dealer_token, gid)
        joined = _join_by_token(client, player_token, invite_tok)
        player_pid = joined["id"]

        _start(client, dealer_token, gid)

        parts = _get_participants(client, dealer_token, gid)
        dealer_pid = next(p["id"] for p in parts if p["role_in_game"] == "dealer")

        _add_buy_in(client, dealer_token, gid, dealer_pid, "100.00", "1000")
        _add_buy_in(client, dealer_token, gid, player_pid, "100.00", "1000")
        _set_final_stack(client, dealer_token, gid, dealer_pid, "1200")
        _set_final_stack(client, dealer_token, gid, player_pid, "800")

        # Mark player as left_early
        participant_service.set_participant_status(
            db_session, uuid_mod.UUID(player_pid), ParticipantStatus.left_early
        )
        db_session.commit()

        r = _close(client, dealer_token, gid)
        assert r.status_code == 200, r.text

        settlement = _get_settlement(client, dealer_token, gid)
        assert settlement["is_complete"] is True
        balance_pids = [b["participant_id"] for b in settlement["balances"]]
        assert dealer_pid in balance_pids
        assert player_pid in balance_pids
        # Verify the player has a net_balance (included in calculation)
        player_balance = next(b for b in settlement["balances"] if b["participant_id"] == player_pid)
        assert player_balance["net_balance"] is not None
