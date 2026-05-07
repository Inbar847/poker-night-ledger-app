"""
WebSocket endpoint for realtime game room subscription — Stage 5.

Connection URL:
    ws://<host>/ws/games/{game_id}?token=<access_jwt>

Auth flow (before accept):
  1. Decode and validate the JWT from the `token` query param.
  2. Confirm it is an access token (not refresh).
  3. Look up the user in the database.
  4. Confirm the game exists.
  5. Confirm the user is a participant of the game.

If any step fails the connection is accepted then immediately closed with a
structured error message and an application-level close code:
  4001 — bad / missing / expired token
  4003 — user is not a participant in this game
  4004 — game not found

Rationale for accept-then-close:
  Starlette's WebSocket.close() is only meaningful after the HTTP upgrade
  has been accepted. Sending a close before accept() results in an HTTP 403
  rather than a proper WebSocket close frame with the error code.

Once connected the server keeps the socket alive, waiting for the client to
disconnect. Clients may send arbitrary text (e.g. pings) which are silently
discarded. The server never sends messages directly on this handler; all
outbound messages are initiated by the ConnectionManager.broadcast() calls
in the mutation routers.

Reconnect contract:
  Events are not replayed on reconnect. Clients should re-fetch game state
  via the REST API after reconnecting, then listen for incremental events.
"""

import uuid

import jwt as pyjwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.realtime.manager import manager
from app.realtime.personal_manager import personal_manager
from app.services import game_service, participant_service

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/games/{game_id}")
async def game_room_ws(
    websocket: WebSocket,
    game_id: uuid.UUID,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
) -> None:
    await _handle_connection(websocket, game_id, token, db)


@router.websocket("/ws/user")
async def personal_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
) -> None:
    await _handle_personal_connection(websocket, token, db)


async def _handle_personal_connection(
    websocket: WebSocket,
    token: str,
    db: Session,
) -> None:
    """Personal user-level WebSocket — Stage 26.

    Authenticates via JWT and registers the connection in the personal manager.
    Used for user-level events like game invitation popups.
    """
    # --- Validate JWT ---
    try:
        payload = decode_token(token)
    except pyjwt.InvalidTokenError:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    if payload.get("type") != "access":
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    raw_id: str | None = payload.get("sub")
    if not raw_id:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    try:
        user_uuid = uuid.UUID(raw_id)
    except ValueError:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    user = db.get(User, user_uuid)
    if user is None:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    # --- Accept and register ---
    await websocket.accept()
    personal_manager.connect(user_uuid, websocket)

    try:
        while True:
            # Discard any client messages (pings, etc.)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        personal_manager.disconnect(user_uuid, websocket)


async def _handle_connection(
    websocket: WebSocket,
    game_id: uuid.UUID,
    token: str,
    db: Session,
) -> None:
    # --- Step 1: validate JWT ---
    try:
        payload = decode_token(token)
    except pyjwt.InvalidTokenError:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    if payload.get("type") != "access":
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    raw_id: str | None = payload.get("sub")
    if not raw_id:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    try:
        user_uuid = uuid.UUID(raw_id)
    except ValueError:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    user = db.get(User, user_uuid)
    if user is None:
        await websocket.accept()
        await websocket.send_json({"error": "invalid_token", "code": 4001})
        await websocket.close(code=4001)
        return

    # --- Step 2: game exists ---
    game = game_service.get_game_by_id(db, game_id)
    if game is None:
        await websocket.accept()
        await websocket.send_json({"error": "game_not_found", "code": 4004})
        await websocket.close(code=4004)
        return

    # --- Step 3: participant check ---
    participant = participant_service.get_participant_for_user(db, game_id, user_uuid)
    if participant is None:
        await websocket.accept()
        await websocket.send_json({"error": "not_a_participant", "code": 4003})
        await websocket.close(code=4003)
        return

    # --- Accept and register ---
    await websocket.accept()
    manager.add(game_id, websocket)

    try:
        while True:
            # Discard any client messages (pings, etc.)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(game_id, websocket)
