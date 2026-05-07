"""
Personal WebSocket connection manager — Stage 26.

Single-instance in-memory map of user_id → connected WebSocket set.
Used for user-level events (e.g. game invitation popups) that are not
tied to a specific game room.

A user may have multiple active connections (multiple devices/tabs).
No Redis or distributed pub/sub required for MVP.
"""

import json
import uuid
from typing import Any

from fastapi import WebSocket


class PersonalConnectionManager:
    def __init__(self) -> None:
        # str(user_id) → set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        key = str(user_id)
        if key not in self._connections:
            self._connections[key] = set()
        self._connections[key].add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        key = str(user_id)
        conns = self._connections.get(key)
        if conns:
            conns.discard(websocket)
            if not conns:
                del self._connections[key]

    # ------------------------------------------------------------------
    # Send to user
    # ------------------------------------------------------------------

    async def send_to_user(self, user_id: uuid.UUID, event: dict[str, Any]) -> None:
        """Send a JSON event to every socket for the given user.

        Dead connections are silently removed.
        """
        key = str(user_id)
        conns = self._connections.get(key)
        if not conns:
            return

        message = json.dumps(event, default=str)
        dead: set[WebSocket] = set()

        for ws in list(conns):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001 — stale connection, swallow and clean up
                dead.add(ws)

        for ws in dead:
            conns.discard(ws)
        if not self._connections.get(key):
            self._connections.pop(key, None)

    # ------------------------------------------------------------------
    # Introspection (used in tests)
    # ------------------------------------------------------------------

    def connection_count(self, user_id: uuid.UUID) -> int:
        return len(self._connections.get(str(user_id), set()))


# Module-level singleton — shared across all requests in the process
personal_manager = PersonalConnectionManager()
