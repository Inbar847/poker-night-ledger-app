"""
Friendship service — all business logic for friend requests and the friends list.

Routers must not contain friendship logic; call these functions instead.
"""

import uuid
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.friendship import Friendship, FriendshipStatus
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.friendship import FriendEntry, FriendUserInfo, FriendshipStatusResponse
from app.services import notification_service


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_friendship_or_404(db: Session, friendship_id: uuid.UUID) -> Friendship:
    row = db.get(Friendship, friendship_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found")
    return row


def _existing_record(
    db: Session, user_a: uuid.UUID, user_b: uuid.UUID
) -> Friendship | None:
    """Return any existing row between the two users regardless of direction."""
    return (
        db.query(Friendship)
        .filter(
            or_(
                (Friendship.requester_user_id == user_a) & (Friendship.addressee_user_id == user_b),
                (Friendship.requester_user_id == user_b) & (Friendship.addressee_user_id == user_a),
            )
        )
        .first()
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def send_request(db: Session, requester_id: uuid.UUID, addressee_id: uuid.UUID) -> Friendship:
    """Create a pending friend request.

    Raises 400 if:
    - requester == addressee (self-request)
    - any existing record between the pair exists (pending, accepted, or declined)

    Phase 2 assumption: declined requests block re-request (simplest MVP guard;
    the addressee must remove the declined row before a new request is possible —
    this is fine because declined rows are invisible to the requester).

    Side-effect: creates a friend_request_received notification for the addressee.
    """
    if requester_id == addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a friend request to yourself",
        )

    addressee = db.get(User, addressee_id)
    if addressee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = _existing_record(db, requester_id, addressee_id)
    if existing is not None:
        if existing.status == FriendshipStatus.accepted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already friends",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A friend request between these users already exists",
        )

    friendship = Friendship(
        requester_user_id=requester_id,
        addressee_user_id=addressee_id,
        status=FriendshipStatus.pending,
    )
    db.add(friendship)
    db.flush()  # get friendship.id before commit

    # Notify the addressee that they have received a friend request
    notification_service.create_notification(
        db=db,
        user_id=addressee_id,
        notification_type=NotificationType.friend_request_received,
        data={"from_user_id": str(requester_id), "friendship_id": str(friendship.id)},
    )

    db.commit()
    db.refresh(friendship)
    return friendship


def accept_request(db: Session, friendship_id: uuid.UUID, caller_id: uuid.UUID) -> Friendship:
    """Accept a pending friend request. Only the addressee may accept.

    Side-effect: creates a friend_request_accepted notification for the requester.
    """
    friendship = _get_friendship_or_404(db, friendship_id)

    if friendship.addressee_user_id != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient can accept this request",
        )

    if friendship.status != FriendshipStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is not pending (current status: {friendship.status})",
        )

    friendship.status = FriendshipStatus.accepted
    db.flush()

    # Notify the original requester that their request was accepted
    notification_service.create_notification(
        db=db,
        user_id=friendship.requester_user_id,
        notification_type=NotificationType.friend_request_accepted,
        data={"from_user_id": str(caller_id), "friendship_id": str(friendship_id)},
    )

    db.commit()
    db.refresh(friendship)
    return friendship


def decline_request(db: Session, friendship_id: uuid.UUID, caller_id: uuid.UUID) -> Friendship:
    """Decline a pending friend request. Only the addressee may decline."""
    friendship = _get_friendship_or_404(db, friendship_id)

    if friendship.addressee_user_id != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient can decline this request",
        )

    if friendship.status != FriendshipStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is not pending (current status: {friendship.status})",
        )

    friendship.status = FriendshipStatus.declined
    db.commit()
    db.refresh(friendship)
    return friendship


def remove_friend(db: Session, friendship_id: uuid.UUID, caller_id: uuid.UUID) -> None:
    """Remove an accepted friendship. Either participant may unfriend."""
    friendship = _get_friendship_or_404(db, friendship_id)

    if caller_id not in (friendship.requester_user_id, friendship.addressee_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this friendship",
        )

    if friendship.status != FriendshipStatus.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only remove an accepted friendship",
        )

    db.delete(friendship)
    db.commit()


def list_friends(db: Session, user_id: uuid.UUID) -> list[FriendEntry]:
    """Return all accepted friends for a user, in both requester and addressee directions."""
    rows = (
        db.query(Friendship)
        .filter(
            Friendship.status == FriendshipStatus.accepted,
            or_(
                Friendship.requester_user_id == user_id,
                Friendship.addressee_user_id == user_id,
            ),
        )
        .all()
    )

    result: list[FriendEntry] = []
    for row in rows:
        friend_id = (
            row.addressee_user_id if row.requester_user_id == user_id else row.requester_user_id
        )
        friend_user = db.get(User, friend_id)
        if friend_user is None:
            continue
        result.append(
            FriendEntry(
                friendship_id=row.id,
                friend=FriendUserInfo(
                    id=friend_user.id,
                    full_name=friend_user.full_name,
                    profile_image_url=friend_user.profile_image_url,
                ),
                since=row.created_at,
            )
        )
    return result


def list_incoming_requests(db: Session, user_id: uuid.UUID) -> list[Friendship]:
    """Return all pending requests where user is the addressee."""
    return (
        db.query(Friendship)
        .filter(
            Friendship.addressee_user_id == user_id,
            Friendship.status == FriendshipStatus.pending,
        )
        .all()
    )


def list_outgoing_requests(db: Session, user_id: uuid.UUID) -> list[Friendship]:
    """Return all pending requests where user is the requester."""
    return (
        db.query(Friendship)
        .filter(
            Friendship.requester_user_id == user_id,
            Friendship.status == FriendshipStatus.pending,
        )
        .all()
    )


def are_friends(db: Session, user_id_a: uuid.UUID, user_id_b: uuid.UUID) -> bool:
    """Return True if an accepted friendship exists between the two users (either direction)."""
    row = (
        db.query(Friendship)
        .filter(
            Friendship.status == FriendshipStatus.accepted,
            or_(
                (Friendship.requester_user_id == user_id_a)
                & (Friendship.addressee_user_id == user_id_b),
                (Friendship.requester_user_id == user_id_b)
                & (Friendship.addressee_user_id == user_id_a),
            ),
        )
        .first()
    )
    return row is not None


FriendshipUIStatus = Literal["not_friends", "pending_outgoing", "pending_incoming", "friends"]


def get_friendship_status(
    db: Session, current_user_id: uuid.UUID, target_user_id: uuid.UUID
) -> FriendshipStatusResponse:
    """Return the friendship state between current_user and target for the mobile UI.

    States:
    - not_friends: no relationship (or declined, which is invisible to requester)
    - pending_outgoing: current user sent a request, not yet accepted
    - pending_incoming: target user sent a request to current user
    - friends: accepted friendship
    """
    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot query friendship status with yourself",
        )

    row = _existing_record(db, current_user_id, target_user_id)
    if row is None:
        return FriendshipStatusResponse(status="not_friends", friendship_id=None)

    if row.status == FriendshipStatus.accepted:
        return FriendshipStatusResponse(status="friends", friendship_id=row.id)

    if row.status == FriendshipStatus.pending:
        if row.requester_user_id == current_user_id:
            return FriendshipStatusResponse(status="pending_outgoing", friendship_id=row.id)
        else:
            return FriendshipStatusResponse(status="pending_incoming", friendship_id=row.id)

    # declined — invisible to requester, treat as not_friends for UI
    return FriendshipStatusResponse(status="not_friends", friendship_id=None)
