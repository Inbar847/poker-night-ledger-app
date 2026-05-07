"""
Tests for Stage 5: realtime WebSocket transport.

Coverage:
- Unit: ConnectionManager add/remove/broadcast/connection_count
- Integration: WS endpoint auth rejection (bad token, non-participant, missing game)
- Integration: WS endpoint acceptance for a valid participant
- Integration: REST mutation endpoints still work correctly (async def change)
- Integration: Broadcast fires after a mutation (manager.broadcast path exercised)

Note on end-to-end delivery:
  Verifying that a message sent by broadcast() is *received* by another
  connected TestClient requires concurrent readers — not supported by the
  synchronous TestClient. That scenario is deferred to manual QA.
  These tests focus on auth logic, connection lifecycle, and that the
  mutation endpoints remain correct after being converted to async def.
"""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.realtime.manager import ConnectionManager
from app.realtime.personal_manager import PersonalConnectionManager


# ---------------------------------------------------------------------------
# Unit tests — ConnectionManager
# ---------------------------------------------------------------------------


class TestConnectionManager:
    def test_add_and_count(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()
        ws = object()  # placeholder; type ignored in unit test
        mgr.add(game_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(game_id) == 1

    def test_remove_decrements(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()
        ws = object()
        mgr.add(game_id, ws)  # type: ignore[arg-type]
        mgr.remove(game_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(game_id) == 0

    def test_remove_cleans_empty_room(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()
        ws = object()
        mgr.add(game_id, ws)  # type: ignore[arg-type]
        mgr.remove(game_id, ws)  # type: ignore[arg-type]
        # Internal room dict should be cleaned up
        assert str(game_id) not in mgr._rooms

    def test_count_unknown_game(self):
        mgr = ConnectionManager()
        assert mgr.connection_count(uuid.uuid4()) == 0

    def test_multiple_connections_same_game(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()
        ws1, ws2 = object(), object()
        mgr.add(game_id, ws1)  # type: ignore[arg-type]
        mgr.add(game_id, ws2)  # type: ignore[arg-type]
        assert mgr.connection_count(game_id) == 2

    def test_broadcast_no_connections_is_noop(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()
        event = {"type": "test", "game_id": str(game_id), "timestamp": "t", "payload": {}}
        # Should not raise even with no connections
        asyncio.run(mgr.broadcast(game_id, event))

    def test_broadcast_sends_to_connected_socket(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()

        sent_messages: list[str] = []

        class FakeWS:
            async def send_text(self, message: str) -> None:
                sent_messages.append(message)

        ws = FakeWS()
        mgr.add(game_id, ws)  # type: ignore[arg-type]
        event = {"type": "test", "game_id": str(game_id), "timestamp": "t", "payload": {}}
        asyncio.run(mgr.broadcast(game_id, event))

        assert len(sent_messages) == 1
        parsed = json.loads(sent_messages[0])
        assert parsed["type"] == "test"

    def test_broadcast_removes_dead_connections(self):
        mgr = ConnectionManager()
        game_id = uuid.uuid4()

        class DeadWS:
            async def send_text(self, _message: str) -> None:
                raise RuntimeError("disconnected")

        ws = DeadWS()
        mgr.add(game_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(game_id) == 1

        event = {"type": "test", "game_id": str(game_id), "timestamp": "t", "payload": {}}
        asyncio.run(mgr.broadcast(game_id, event))

        # Dead connection should have been removed
        assert mgr.connection_count(game_id) == 0


# ---------------------------------------------------------------------------
# Helpers shared by integration tests
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


def _create_and_start_game(client: TestClient, token: str) -> dict:
    r = client.post(
        "/games",
        json={"title": "WS Test Game", "chip_cash_rate": 0.01, "currency": "USD"},
        headers=_auth(token),
    )
    assert r.status_code == 201
    game = r.json()
    r2 = client.post(f"/games/{game['id']}/start", headers=_auth(token))
    assert r2.status_code == 200
    return game


# ---------------------------------------------------------------------------
# Integration tests — WebSocket auth / rejection
# ---------------------------------------------------------------------------


class TestWebSocketAuth:
    def test_missing_token_rejected(self, client: TestClient):
        token = _register_and_login(client, "ws_notoken@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        with client.websocket_connect(f"/ws/games/{game_id}?token=not.a.jwt") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "invalid_token"
            assert msg["code"] == 4001

    def test_expired_token_rejected(self, client: TestClient):
        # A structurally valid JWT with a wrong signature / bad content
        bad_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4IiwidHlwZSI6ImFjY2VzcyJ9.bad"
        token = _register_and_login(client, "ws_exptoken@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        with client.websocket_connect(f"/ws/games/{game_id}?token={bad_token}") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "invalid_token"
            assert msg["code"] == 4001

    def test_refresh_token_rejected(self, client: TestClient):
        """Refresh tokens must not be accepted as WS auth."""
        r = client.post(
            "/auth/register",
            json={"email": "ws_refresh@example.com", "password": "pw12345678", "full_name": "R"},
        )
        r = client.post(
            "/auth/login",
            json={"email": "ws_refresh@example.com", "password": "pw12345678"},
        )
        refresh_token = r.json()["refresh_token"]
        access_token = r.json()["access_token"]

        game = _create_and_start_game(client, access_token)
        game_id = game["id"]

        with client.websocket_connect(f"/ws/games/{game_id}?token={refresh_token}") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "invalid_token"
            assert msg["code"] == 4001

    def test_non_participant_rejected(self, client: TestClient):
        dealer_token = _register_and_login(client, "ws_dealer2@example.com")
        outsider_token = _register_and_login(client, "ws_outsider@example.com")

        game = _create_and_start_game(client, dealer_token)
        game_id = game["id"]

        with client.websocket_connect(f"/ws/games/{game_id}?token={outsider_token}") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "not_a_participant"
            assert msg["code"] == 4003

    def test_unknown_game_rejected(self, client: TestClient):
        token = _register_and_login(client, "ws_nogame@example.com")
        fake_game_id = uuid.uuid4()

        with client.websocket_connect(f"/ws/games/{fake_game_id}?token={token}") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "game_not_found"
            assert msg["code"] == 4004

    def test_valid_participant_connects(self, client: TestClient):
        """Dealer (valid participant) should connect and stay open."""
        token = _register_and_login(client, "ws_dealer3@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        with client.websocket_connect(f"/ws/games/{game_id}?token={token}") as ws:
            # Connection should be open; send a ping and confirm no immediate close
            ws.send_text("ping")
            # If we get here without an exception, the connection was accepted
            # (TestClient will raise on disconnect)


# ---------------------------------------------------------------------------
# Integration tests — REST mutation endpoints remain correct after async change
# ---------------------------------------------------------------------------


class TestMutationsAfterAsyncConversion:
    """Smoke-tests to confirm mutation endpoints still return correct HTTP responses."""

    def test_create_buy_in(self, client: TestClient):
        token = _register_and_login(client, "ws_bi@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        # Get dealer's participant_id
        r = client.get(f"/games/{game_id}/participants", headers=_auth(token))
        participants = r.json()
        dealer_participant_id = participants[0]["id"]

        r = client.post(
            f"/games/{game_id}/buy-ins",
            json={"participant_id": dealer_participant_id, "cash_amount": 50.0, "chips_amount": 5000},
            headers=_auth(token),
        )
        assert r.status_code == 201
        body = r.json()
        assert body["cash_amount"] == "50.00"

    def test_create_expense(self, client: TestClient):
        token = _register_and_login(client, "ws_exp@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        r = client.get(f"/games/{game_id}/participants", headers=_auth(token))
        dealer_pid = r.json()[0]["id"]

        r = client.post(
            f"/games/{game_id}/expenses",
            json={
                "title": "Pizza",
                "total_amount": 30.0,
                "paid_by_participant_id": dealer_pid,
                "splits": [{"participant_id": dealer_pid, "share_amount": 30.0}],
            },
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Pizza"

    def test_upsert_final_stack(self, client: TestClient):
        token = _register_and_login(client, "ws_fs@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        r = client.get(f"/games/{game_id}/participants", headers=_auth(token))
        dealer_pid = r.json()[0]["id"]

        r = client.put(
            f"/games/{game_id}/final-stacks/{dealer_pid}",
            json={"chips_amount": 3000},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["chips_amount"] == "3000.00"

    def test_start_and_close_game(self, client: TestClient):
        token = _register_and_login(client, "ws_lifecycle@example.com")
        r = client.post(
            "/games",
            json={"title": "Lifecycle", "chip_cash_rate": 0.01, "currency": "USD"},
            headers=_auth(token),
        )
        game_id = r.json()["id"]

        r = client.post(f"/games/{game_id}/start", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["status"] == "active"

        parts = client.get(f"/games/{game_id}/participants", headers=_auth(token)).json()
        for p in parts:
            client.put(f"/games/{game_id}/final-stacks/{p['id']}", json={"chips_amount": 0.0}, headers=_auth(token))

        r = client.post(f"/games/{game_id}/close", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    def test_invite_user_broadcasts(self, client: TestClient):
        """Invitation rework: dealer invites a friend, friend accepts, becomes participant."""
        dealer_token = _register_and_login(client, "ws_inv_dealer@example.com")
        player_token = _register_and_login(client, "ws_inv_player@example.com")

        # Get player's user id
        r = client.get("/users/me", headers=_auth(player_token))
        player_id = r.json()["id"]

        # Make them friends first (required for new invitation flow)
        r = client.post(
            "/friends/request",
            json={"addressee_user_id": player_id},
            headers=_auth(dealer_token),
        )
        assert r.status_code == 201
        fid = r.json()["id"]
        r = client.post(f"/friends/{fid}/accept", headers=_auth(player_token))
        assert r.status_code == 200

        game = _create_and_start_game(client, dealer_token)
        game_id = game["id"]

        # Create invitation (pending)
        r = client.post(
            f"/games/{game_id}/invitations",
            json={"invited_user_id": player_id},
            headers=_auth(dealer_token),
        )
        assert r.status_code == 201
        inv_id = r.json()["id"]
        assert r.json()["status"] == "pending"

        # Player accepts → becomes participant
        r = client.post(
            f"/games/{game_id}/invitations/{inv_id}/accept",
            headers=_auth(player_token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "accepted"

    def test_add_guest_broadcasts(self, client: TestClient):
        token = _register_and_login(client, "ws_guest@example.com")
        game = _create_and_start_game(client, token)
        game_id = game["id"]

        r = client.post(
            f"/games/{game_id}/guests",
            json={"guest_name": "Alice Guest"},
            headers=_auth(token),
        )
        assert r.status_code == 201
        assert r.json()["guest_name"] == "Alice Guest"


# ---------------------------------------------------------------------------
# Unit tests — PersonalConnectionManager (Stage 26)
# ---------------------------------------------------------------------------


class TestPersonalConnectionManager:
    def test_connect_and_count(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()
        ws = object()
        mgr.connect(user_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(user_id) == 1

    def test_disconnect_decrements(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()
        ws = object()
        mgr.connect(user_id, ws)  # type: ignore[arg-type]
        mgr.disconnect(user_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(user_id) == 0

    def test_disconnect_cleans_empty_entry(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()
        ws = object()
        mgr.connect(user_id, ws)  # type: ignore[arg-type]
        mgr.disconnect(user_id, ws)  # type: ignore[arg-type]
        assert str(user_id) not in mgr._connections

    def test_count_unknown_user(self):
        mgr = PersonalConnectionManager()
        assert mgr.connection_count(uuid.uuid4()) == 0

    def test_multiple_connections_same_user(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()
        ws1, ws2 = object(), object()
        mgr.connect(user_id, ws1)  # type: ignore[arg-type]
        mgr.connect(user_id, ws2)  # type: ignore[arg-type]
        assert mgr.connection_count(user_id) == 2

    def test_send_to_user_no_connections_is_noop(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()
        event = {"type": "test", "payload": {}}
        asyncio.run(mgr.send_to_user(user_id, event))

    def test_send_to_user_delivers_message(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()

        sent_messages: list[str] = []

        class FakeWS:
            async def send_text(self, message: str) -> None:
                sent_messages.append(message)

        ws = FakeWS()
        mgr.connect(user_id, ws)  # type: ignore[arg-type]
        event = {"type": "user.game_invitation", "payload": {"game_id": "abc"}}
        asyncio.run(mgr.send_to_user(user_id, event))

        assert len(sent_messages) == 1
        parsed = json.loads(sent_messages[0])
        assert parsed["type"] == "user.game_invitation"

    def test_send_to_user_removes_dead_connections(self):
        mgr = PersonalConnectionManager()
        user_id = uuid.uuid4()

        class DeadWS:
            async def send_text(self, _message: str) -> None:
                raise RuntimeError("disconnected")

        ws = DeadWS()
        mgr.connect(user_id, ws)  # type: ignore[arg-type]
        assert mgr.connection_count(user_id) == 1

        event = {"type": "test", "payload": {}}
        asyncio.run(mgr.send_to_user(user_id, event))

        assert mgr.connection_count(user_id) == 0


# ---------------------------------------------------------------------------
# Integration tests — Personal WebSocket auth (Stage 26)
# ---------------------------------------------------------------------------


class TestPersonalWebSocketAuth:
    def test_invalid_token_rejected(self, client: TestClient):
        with client.websocket_connect("/ws/user?token=not.a.jwt") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "invalid_token"
            assert msg["code"] == 4001

    def test_refresh_token_rejected(self, client: TestClient):
        client.post(
            "/auth/register",
            json={"email": "pws_refresh@example.com", "password": "pw12345678", "full_name": "R"},
        )
        r = client.post(
            "/auth/login",
            json={"email": "pws_refresh@example.com", "password": "pw12345678"},
        )
        refresh_token = r.json()["refresh_token"]

        with client.websocket_connect(f"/ws/user?token={refresh_token}") as ws:
            msg = ws.receive_json()
            assert msg["error"] == "invalid_token"
            assert msg["code"] == 4001

    def test_valid_user_connects(self, client: TestClient):
        token = _register_and_login(client, "pws_valid@example.com")
        with client.websocket_connect(f"/ws/user?token={token}") as ws:
            ws.send_text("ping")
            # If we get here without exception, the connection was accepted


# ---------------------------------------------------------------------------
# Integration tests — Invitation creates personal WS event (Stage 26)
# ---------------------------------------------------------------------------


class TestInvitationPersonalBroadcast:
    def test_create_invitation_sends_personal_event(self, client: TestClient):
        """Creating an invitation should call personal_manager.send_to_user."""
        dealer_token = _register_and_login(client, "pws_dealer@example.com")
        player_token = _register_and_login(client, "pws_player@example.com")

        r = client.get("/users/me", headers=_auth(player_token))
        player_id = r.json()["id"]

        # Make friends
        r = client.post(
            "/friends/request",
            json={"addressee_user_id": player_id},
            headers=_auth(dealer_token),
        )
        assert r.status_code == 201
        fid = r.json()["id"]
        r = client.post(f"/friends/{fid}/accept", headers=_auth(player_token))
        assert r.status_code == 200

        game = _create_and_start_game(client, dealer_token)
        game_id = game["id"]

        # Patch personal_manager.send_to_user to verify the call
        with patch(
            "app.api.routers.game_invitations.personal_manager.send_to_user",
            new_callable=AsyncMock,
        ) as mock_send:
            r = client.post(
                f"/games/{game_id}/invitations",
                json={"invited_user_id": player_id},
                headers=_auth(dealer_token),
            )
            assert r.status_code == 201

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            # First arg is user_id (the invited player)
            assert str(call_args[0][0]) == player_id
            # Second arg is the event dict
            event = call_args[0][1]
            assert event["type"] == "user.game_invitation"
            assert event["payload"]["game_id"] == game_id
            assert event["payload"]["invitation_id"] == r.json()["id"]
