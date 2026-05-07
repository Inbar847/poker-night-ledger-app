"""
Settlement router — Stage 4.

GET /games/{game_id}/settlement       → summary balances + transfers
GET /games/{game_id}/settlement/audit → full audit with line items

Access rules:
- Game must be closed (409 if not).
- Caller must be a participant in the game (403 if not).
- Both endpoints are read-only; no dealer-only restriction.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.game import Game, GameStatus
from app.models.user import User
from app.schemas.settlement import SettlementAuditResponse, SettlementResponse
from app.services import game_service, participant_service, settlement_service

router = APIRouter(prefix="/games", tags=["settlement"])


def _get_closed_game_or_error(db: Session, game_id: uuid.UUID) -> Game:
    game = game_service.get_game_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    if game.status != GameStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Settlement is only available for closed games. "
                f"Current status: '{game.status.value}'."
            ),
        )
    return game


def _require_participant(db: Session, game_id: uuid.UUID, user_id: uuid.UUID) -> None:
    p = participant_service.get_participant_for_user(db, game_id, user_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this game",
        )


@router.get(
    "/{game_id}/settlement",
    response_model=SettlementResponse,
)
def get_settlement(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettlementResponse:
    game = _get_closed_game_or_error(db, game_id)
    _require_participant(db, game_id, current_user.id)
    return settlement_service.get_settlement(db, game)


@router.get(
    "/{game_id}/settlement/audit",
    response_model=SettlementAuditResponse,
)
def get_settlement_audit(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettlementAuditResponse:
    game = _get_closed_game_or_error(db, game_id)
    _require_participant(db, game_id, current_user.id)
    return settlement_service.get_settlement_audit(db, game)
