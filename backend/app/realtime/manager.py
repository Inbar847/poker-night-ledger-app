"""
WebSocket connection manager — Stage 5.

Single-instance in-memory map of game_id → connected WebSocket set.
No Redis or distributed pub/sub required for MVP.

Thread safety note:
  FastAPI runs async route handlers on the event loop thread.
  WebSocket connections and broadcasts all happen on the same event loop,
  so no locking is needed for the in-memory dict.
"""

import json
import uuid
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # str(game_id) → set of active WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def add(self, game_id: uuid.UUID, websocket: WebSocket) -> None:
        key = str(game_id)
        if key not in self._rooms:
            self._rooms[key] = set()
        self._rooms[key].add(websocket)

    def remove(self, game_id: uuid.UUID, websocket: WebSocket) -> None:
        key = str(game_id)
        room = self._rooms.get(key)
        if room:
            room.discard(websocket)
            if not room:
                del self._rooms[key]

    # ------------------------------------------------------------------
    # Broadcast
    # ------------------------------------------------------------------

    async def broadcast(self, game_id: uuid.UUID, event: dict[str, Any]) -> None:
        """Send a JSON event to every socket in the game room.

        Dead connections are silently removed.
        """
        key = str(game_id)
        room = self._rooms.get(key)
        if not room:
            return

        message = json.dumps(event, default=str)
        dead: set[WebSocket] = set()

        for ws in list(room):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001 — stale connection, swallow and clean up
                dead.add(ws)

        for ws in dead:
            room.discard(ws)
        if not self._rooms.get(key):
            self._rooms.pop(key, None)

    # ------------------------------------------------------------------
    # Introspection (used in tests)
    # ------------------------------------------------------------------

    def connection_count(self, game_id: uuid.UUID) -> int:
        return len(self._rooms.get(str(game_id), set()))


# Module-level singleton — shared across all requests in the process
manager = ConnectionManager()
