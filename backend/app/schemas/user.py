import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSearchResult(BaseModel):
    """Public-safe fields returned from /users/search — no email or phone exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    profile_image_url: str | None


class PublicProfileResponse(BaseModel):
    """Public profile for /users/{user_id}/profile — visible to any authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    profile_image_url: str | None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    phone: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    profile_image_url: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    phone: str | None
    profile_image_url: str | None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
