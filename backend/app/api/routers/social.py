"""
Social router — Stage 17.

Endpoints:
  GET /social/leaderboard  — friend leaderboard for the current user
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User  # noqa: F401 — type hint for Depends
from app.schemas.stats import LeaderboardResponse
from app.services import stats_service

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeaderboardResponse:
    """
    Return a ranked list of the current user + all accepted friends.

    Sorted by cumulative net result (descending).
    Only includes accepted friends — never exposes non-friend data.
    """
    return stats_service.get_leaderboard(db, current_user.id)
