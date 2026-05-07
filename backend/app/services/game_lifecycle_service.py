"""
Game lifecycle service — extracted close-game business logic.

Handles:
- Validation that all settlement-eligible participants have final stacks
- Shortage computation and strategy application
- Game state transition (active → closed)
- Notification creation (game_closed + settlement_owed for debtors)

The router remains responsible for HTTP concerns (Depends, HTTPException)
and WebSocket broadcasts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.ledger import FinalStack
from app.models.notification import NotificationType
from app.models.participant import Participant
from app.models.user import User
from app.schemas.game import GameResponse, ShortageResolutionRequired
from app.services import (
    game_service,
    notification_service,
    participant_service,
    settlement_service,
)
from app.services.settlement_service import _build_calcs, compute_shortage_amount


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


@dataclass
class MissingFinalStackEntry:
    participant_id: uuid.UUID
    display_name: str


class MissingFinalStacksError(Exception):
    """Raised when close is attempted but some participants lack final stacks."""

    def __init__(self, missing: list[MissingFinalStackEntry]) -> None:
        self.missing = missing
        names = ", ".join(m.display_name for m in missing)
        super().__init__(f"Cannot close game: missing final chip counts for: {names}")


class GameNotActiveError(Exception):
    """Raised when a state transition is attempted on a non-active game."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _display_name(participant: Participant, user: User | None) -> str:
    if participant.guest_name:
        return participant.guest_name
    if user and user.full_name:
        return user.full_name
    if user:
        return user.email
    return f"Player ({str(participant.id)[:8]})"


def _load_users_by_id(
    db: Session, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, User]:
    if not user_ids:
        return {}
    result: dict[uuid.UUID, User] = {}
    for u in db.query(User).filter(User.id.in_(user_ids)).all():
        result[u.id] = u
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class CloseGameResult:
    """Return value from close_and_finalize.

    If `shortage_resolution_required` is not None, the game was NOT closed and
    the caller should return that Pydantic model as the HTTP response.
    Otherwise `game_response` contains the closed game.
    """

    game_response: GameResponse | None = None
    shortage_resolution_required: ShortageResolutionRequired | None = None


def close_and_finalize(
    db: Session,
    game: Game,
    strategy: str | None,
) -> CloseGameResult:
    """
    Validate, compute shortage, close game, and create notifications.

    Raises:
        MissingFinalStacksError: when settlement-eligible participants lack
            final stacks.
        GameNotActiveError: when the game is not in active status.

    Returns a CloseGameResult. The caller must inspect it:
    - If shortage_resolution_required is set, the game was NOT closed and
      the caller should return the ShortageResolutionRequired body.
    - Otherwise game_response is the closed game.

    The caller is responsible for calling db.commit() after this function
    returns (to keep HTTP/transaction control in the router) and for
    broadcasting WebSocket events.
    """

    game_id = game.id

    # --- Validate all settlement-eligible participants have final stacks ---
    eligible = participant_service.get_settlement_eligible_participants(db, game_id)
    final_stack_pids = {
        fs.participant_id
        for fs in db.query(FinalStack).filter(FinalStack.game_id == game_id).all()
    }

    user_ids = [p.user_id for p in eligible if p.user_id is not None]
    users_by_id = _load_users_by_id(db, user_ids)

    missing = [
        MissingFinalStackEntry(
            participant_id=p.id,
            display_name=_display_name(
                p, users_by_id.get(p.user_id) if p.user_id else None
            ),
        )
        for p in eligible
        if p.id not in final_stack_pids
    ]

    if missing:
        raise MissingFinalStacksError(missing)

    # --- Compute shortage ---
    calcs = _build_calcs(db, game)
    shortage = compute_shortage_amount(calcs)

    if shortage > 0 and not strategy:
        return CloseGameResult(
            shortage_resolution_required=ShortageResolutionRequired(
                shortage_amount=shortage,
                available_strategies=["proportional_winners", "equal_all"],
            )
        )

    # Store shortage on the game before closing
    if shortage > 0 and strategy:
        game.shortage_amount = shortage
        game.shortage_strategy = strategy
        db.flush()

    # --- Close the game ---
    try:
        result = game_service.close_game(db, game)
    except ValueError as exc:
        raise GameNotActiveError(str(exc)) from exc

    # --- Create game_closed notifications for all registered participants ---
    participants = participant_service.get_participants(db, game_id)
    for p in participants:
        if p.user_id is not None:
            notification_service.create_notification(
                db,
                user_id=p.user_id,
                notification_type=NotificationType.game_closed,
                data={"game_id": str(game_id)},
            )

    # --- Create settlement_owed notifications for registered debtors ---
    settlement = settlement_service.get_settlement(db, game)
    if settlement.is_complete:
        pid_to_user: dict[uuid.UUID, uuid.UUID] = {
            p.id: p.user_id for p in participants if p.user_id is not None
        }
        for transfer in settlement.transfers:
            debtor_user_id = pid_to_user.get(transfer.from_participant_id)
            if debtor_user_id is not None:
                notification_service.create_notification(
                    db,
                    user_id=debtor_user_id,
                    notification_type=NotificationType.settlement_owed,
                    data={
                        "game_id": str(game_id),
                        "game_title": game.title,
                        "to_display_name": transfer.to_display_name,
                        "amount": str(transfer.amount),
                        "currency": game.currency,
                    },
                )

    # Caller must db.commit() and broadcast events
    return CloseGameResult(game_response=result)
