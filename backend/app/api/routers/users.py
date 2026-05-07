import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.stats import UserStatsView
from app.schemas.user import PublicProfileResponse, UserResponse, UserSearchResult, UserUpdate
from app.services import stats_service, user_service
from app.services.user_service import update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return update_user(db, current_user, data)


@router.get("/search", response_model=list[UserSearchResult])
def search_users(
    q: str = Query(default="", description="Name or email prefix to search"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserSearchResult]:
    """
    Search registered users by name (partial, case-insensitive).

    Returns public-safe fields only (id, full_name, profile_image_url).
    Email is not searchable and is never included in results.
    The requesting user is excluded from results.
    Queries shorter than 2 characters return an empty list.
    """
    rows = user_service.search_users(db, q, current_user.id)
    return [UserSearchResult.model_validate(u) for u in rows]


@router.get("/{user_id}/profile", response_model=PublicProfileResponse)
def get_public_profile(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PublicProfileResponse:
    """Return the public profile for any registered user."""
    user = user_service.get_public_profile(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return PublicProfileResponse.model_validate(user)


@router.get("/{user_id}/stats", response_model=UserStatsView)
def get_user_stats(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStatsView:
    """
    Return stats for the given user.

    Full stats are returned if the viewer is the user themselves or an accepted friend.
    Non-friends receive only total_games_played with is_friend_access=False.
    Privacy is enforced in the stats service, not here.
    """
    # Verify the target user exists
    target = user_service.get_public_profile(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return stats_service.get_user_stats_view(
        db=db,
        target_user_id=user_id,
        viewer_user_id=current_user.id,
    )
