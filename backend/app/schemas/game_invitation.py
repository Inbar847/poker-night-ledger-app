import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GameInvitationCreate(BaseModel):
    invited_user_id: uuid.UUID


class GameInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    invited_user_id: uuid.UUID
    invited_user_display_name: str
    invited_by_user_id: uuid.UUID
    status: str
    created_at: datetime


class GameInvitationListResponse(BaseModel):
    invitations: list[GameInvitationResponse]
