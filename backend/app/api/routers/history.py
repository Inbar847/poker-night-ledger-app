"""
History and stats router — Stage 8.

Endpoints:
  GET /history/games              — closed games the user participated in
  GET /history/games/{game_id}    — settlement detail for one historical game
  GET /stats/me                   — personal stats aggregates
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.settlement import SettlementResponse
from app.schemas.stats import GameHistoryItem, UserStats
from app.services import stats_service

router = APIRouter(tags=["history"])


@router.get("/history/games", response_model=list[GameHistoryItem])
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GameHistoryItem]:
    """Return all closed games in which the current user was a registered participant."""
    return stats_service.get_history(db, current_user.id)


@router.get("/history/games/{game_id}", response_model=SettlementResponse)
def get_history_game(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettlementResponse:
    """
    Return the full settlement view for one historical (closed) game.
    404 if the game is not closed or the user was not a participant.
    """
    result = stats_service.get_history_game(db, game_id, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found or not accessible",
        )
    return result


@router.get("/stats/me", response_model=UserStats)
def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStats:
    """Return personal statistics for the current authenticated user."""
    return stats_service.get_stats(db, current_user.id)
