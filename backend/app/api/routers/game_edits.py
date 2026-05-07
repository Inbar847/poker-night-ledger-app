"""
Game edits router — retroactive editing of closed games (Stage 28).

Endpoints:
  GET    /games/{game_id}/edits                              — audit trail
  POST   /games/{game_id}/edits/buy-ins                      — add buy-in
  PATCH  /games/{game_id}/edits/buy-ins/{buyin_id}           — edit buy-in
  DELETE /games/{game_id}/edits/buy-ins/{buyin_id}           — delete buy-in
  PATCH  /games/{game_id}/edits/final-stacks/{participant_id} — edit final stack
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.game import Game
from app.models.participant import Participant, RoleInGame
from app.models.user import User
from app.schemas.game_edit import (
    ClosedGameBuyInCreate,
    ClosedGameBuyInUpdate,
    ClosedGameFinalStackUpdate,
    GameEditResponse,
)
from app.schemas.ledger import BuyInResponse
from app.schemas.ledger import FinalStackResponse
from app.services import game_edit_service, game_service, participant_service

router = APIRouter(prefix="/games/{game_id}/edits", tags=["game-edits"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_game_or_404(db: Session, game_id: uuid.UUID) -> Game:
    game = game_service.get_game_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


def _get_participant_or_403(db: Session, game_id: uuid.UUID, user_id: uuid.UUID) -> Participant:
    p = participant_service.get_participant_for_user(db, game_id, user_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this game",
        )
    return p


def _require_dealer(participant: Participant) -> None:
    if participant.role_in_game != RoleInGame.dealer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealer access required",
        )


def _display_name(participant: Participant, user: User | None) -> str:
    if participant.guest_name:
        return participant.guest_name
    if user and user.full_name:
        return user.full_name
    if user:
        return user.email
    return f"Player ({str(participant.id)[:8]})"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[GameEditResponse])
def list_edits(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GameEditResponse]:
    """List the audit trail for a game. Any participant can view."""
    _get_game_or_404(db, game_id)
    _get_participant_or_403(db, game_id, current_user.id)

    edits = game_edit_service.list_edits_for_game(db, game_id)

    # Load editor display names
    editor_ids = list({e.edited_by_user_id for e in edits})
    editors_by_id: dict[uuid.UUID, User] = {}
    if editor_ids:
        for u in db.query(User).filter(User.id.in_(editor_ids)).all():
            editors_by_id[u.id] = u

    return [
        GameEditResponse(
            id=e.id,
            game_id=e.game_id,
            edited_by_user_id=e.edited_by_user_id,
            edited_by_display_name=(
                editors_by_id[e.edited_by_user_id].full_name
                or editors_by_id[e.edited_by_user_id].email
                if e.edited_by_user_id in editors_by_id
                else "Unknown"
            ),
            edit_type=e.edit_type,
            entity_id=e.entity_id,
            before_data=e.before_data,
            after_data=e.after_data,
            created_at=e.created_at,
        )
        for e in edits
    ]


@router.post("/buy-ins", response_model=BuyInResponse, status_code=status.HTTP_201_CREATED)
def create_buyin(
    game_id: uuid.UUID,
    data: ClosedGameBuyInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyInResponse:
    """Add a buy-in to a closed game. Dealer only."""
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    try:
        buyin = game_edit_service.create_closed_game_buyin(db, game, data, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BuyInResponse.model_validate(buyin)


@router.patch("/buy-ins/{buyin_id}", response_model=BuyInResponse)
def update_buyin(
    game_id: uuid.UUID,
    buyin_id: uuid.UUID,
    data: ClosedGameBuyInUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyInResponse:
    """Edit a buy-in on a closed game. Dealer only."""
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    try:
        buyin = game_edit_service.edit_closed_game_buyin(
            db, game, buyin_id, data, current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return BuyInResponse.model_validate(buyin)


@router.delete("/buy-ins/{buyin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_buyin(
    game_id: uuid.UUID,
    buyin_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a buy-in from a closed game. Dealer only."""
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    try:
        game_edit_service.delete_closed_game_buyin(db, game, buyin_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/final-stacks/{participant_id}", response_model=FinalStackResponse)
def update_final_stack(
    game_id: uuid.UUID,
    participant_id: uuid.UUID,
    data: ClosedGameFinalStackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinalStackResponse:
    """Edit a final stack on a closed game. Dealer only."""
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    try:
        fs = game_edit_service.edit_closed_game_final_stack(
            db, game, participant_id, data, current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return FinalStackResponse.model_validate(fs)
