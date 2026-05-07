import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.participant import ParticipantStatus, ParticipantType, RoleInGame


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    user_id: uuid.UUID | None
    guest_name: str | None
    display_name: str
    participant_type: ParticipantType
    role_in_game: RoleInGame
    status: ParticipantStatus = ParticipantStatus.active
    joined_at: datetime


class InviteUserRequest(BaseModel):
    user_id: uuid.UUID


class AddGuestRequest(BaseModel):
    guest_name: str = Field(min_length=1, max_length=255)

    @field_validator("guest_name", mode="before")
    @classmethod
    def strip_and_require_non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("guest_name must not be blank or whitespace-only.")
        return stripped


class JoinByTokenRequest(BaseModel):
    token: str
