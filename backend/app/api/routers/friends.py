"""
Friends router — thin controller that delegates all logic to friendship_service.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.friendship import (
    FriendEntry,
    FriendRequestCreate,
    FriendshipResponse,
    FriendshipStatusResponse,
    FriendUserInfo,
    IncomingRequestEntry,
    OutgoingRequestEntry,
)
from app.services import friendship_service

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post(
    "/request",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request(
    body: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friendship_service.send_request(
        db=db,
        requester_id=current_user.id,
        addressee_id=body.addressee_user_id,
    )


@router.post(
    "/{friendship_id}/accept",
    response_model=FriendshipResponse,
)
def accept_friend_request(
    friendship_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friendship_service.accept_request(
        db=db,
        friendship_id=friendship_id,
        caller_id=current_user.id,
    )


@router.post(
    "/{friendship_id}/decline",
    response_model=FriendshipResponse,
)
def decline_friend_request(
    friendship_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friendship_service.decline_request(
        db=db,
        friendship_id=friendship_id,
        caller_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[FriendEntry],
)
def get_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return friendship_service.list_friends(db=db, user_id=current_user.id)


@router.get(
    "/requests/incoming",
    response_model=list[IncomingRequestEntry],
)
def get_incoming_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return pending incoming requests enriched with the requester's user info."""
    rows = friendship_service.list_incoming_requests(db=db, user_id=current_user.id)
    result: list[IncomingRequestEntry] = []
    for row in rows:
        requester = db.get(User, row.requester_user_id)
        if requester is None:
            continue
        result.append(
            IncomingRequestEntry(
                id=row.id,
                requester=FriendUserInfo(
                    id=requester.id,
                    full_name=requester.full_name,
                    profile_image_url=requester.profile_image_url,
                ),
                status=row.status,
                created_at=row.created_at,
            )
        )
    return result


@router.get(
    "/requests/outgoing",
    response_model=list[OutgoingRequestEntry],
)
def get_outgoing_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return pending outgoing requests enriched with the addressee's user info."""
    rows = friendship_service.list_outgoing_requests(db=db, user_id=current_user.id)
    result: list[OutgoingRequestEntry] = []
    for row in rows:
        addressee = db.get(User, row.addressee_user_id)
        if addressee is None:
            continue
        result.append(
            OutgoingRequestEntry(
                id=row.id,
                addressee=FriendUserInfo(
                    id=addressee.id,
                    full_name=addressee.full_name,
                    profile_image_url=addressee.profile_image_url,
                ),
                status=row.status,
                created_at=row.created_at,
            )
        )
    return result


@router.get(
    "/status/{user_id}",
    response_model=FriendshipStatusResponse,
)
def get_friendship_status(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the friendship state between the current user and the target user.

    Used by PublicProfileScreen to show the correct Add Friend / Pending / Friends button.
    """
    return friendship_service.get_friendship_status(
        db=db,
        current_user_id=current_user.id,
        target_user_id=user_id,
    )


@router.delete(
    "/{friendship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_friend(
    friendship_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    friendship_service.remove_friend(
        db=db,
        friendship_id=friendship_id,
        caller_id=current_user.id,
    )
