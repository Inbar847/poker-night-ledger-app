import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.friendship import FriendshipStatus


class FriendRequestCreate(BaseModel):
    addressee_user_id: uuid.UUID


class FriendshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requester_user_id: uuid.UUID
    addressee_user_id: uuid.UUID
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime


class FriendUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    profile_image_url: str | None


class FriendEntry(BaseModel):
    friendship_id: uuid.UUID
    friend: FriendUserInfo
    since: datetime


# ---------------------------------------------------------------------------
# Enriched request entries — include the other party's user info for the UI
# so it can show name/avatar without a separate fetch.
# ---------------------------------------------------------------------------


class IncomingRequestEntry(BaseModel):
    """Pending incoming request with the requester's public info."""

    id: uuid.UUID
    requester: FriendUserInfo
    status: FriendshipStatus
    created_at: datetime


class OutgoingRequestEntry(BaseModel):
    """Pending outgoing request with the addressee's public info."""

    id: uuid.UUID
    addressee: FriendUserInfo
    status: FriendshipStatus
    created_at: datetime


# ---------------------------------------------------------------------------
# Friendship status for the mobile UI (used by PublicProfileScreen)
# ---------------------------------------------------------------------------

FriendshipUIStatus = Literal["not_friends", "pending_outgoing", "pending_incoming", "friends"]


class FriendshipStatusResponse(BaseModel):
    status: FriendshipUIStatus
    friendship_id: uuid.UUID | None
