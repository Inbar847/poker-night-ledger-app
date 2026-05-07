import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.game import GameStatus


class GameCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    chip_cash_rate: Decimal = Field(gt=0)
    currency: str = Field(default="ILS", max_length=10)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank or whitespace-only.")
        return stripped


class CloseGameRequest(BaseModel):
    """Optional body for POST /games/{id}/close.

    If the settlement has a shortage, shortage_strategy must be provided.
    Omitting the body (or passing null) on a game with no shortage is fine.
    """

    shortage_strategy: str | None = Field(
        default=None,
        description="'proportional_winners' or 'equal_all'. Required if shortage > 0.",
    )

    @field_validator("shortage_strategy", mode="before")
    @classmethod
    def validate_strategy(cls, v: str | None) -> str | None:
        if v is not None and v not in ("proportional_winners", "equal_all"):
            raise ValueError(
                "shortage_strategy must be 'proportional_winners' or 'equal_all'"
            )
        return v


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_by_user_id: uuid.UUID
    dealer_user_id: uuid.UUID
    scheduled_at: datetime | None
    chip_cash_rate: Decimal
    currency: str
    status: GameStatus
    invite_token: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    shortage_amount: Decimal | None = None
    shortage_strategy: str | None = None


class InviteLinkResponse(BaseModel):
    game_id: uuid.UUID
    invite_token: str


class ShortagePreviewResponse(BaseModel):
    """Response for GET /games/{id}/shortage-preview."""

    has_shortage: bool
    shortage_amount: Decimal


class MissingFinalStack(BaseModel):
    """A participant who is missing a final chip count."""

    participant_id: uuid.UUID
    display_name: str


class CashoutRequest(BaseModel):
    """Request body for POST /games/{game_id}/cashout — player enters own final chip count."""

    chips_amount: Decimal = Field(ge=0)


class CashoutResponse(BaseModel):
    """Response for POST /games/{game_id}/cashout."""

    participant_id: uuid.UUID
    chips_amount: Decimal
    status: str  # "left_early"


class ShortageResolutionRequired(BaseModel):
    """Returned by POST /games/{id}/close when a shortage exists but no strategy was provided.

    The game is NOT closed yet. The mobile client should display the shortage
    modal and re-POST /games/{id}/close with the chosen shortage_strategy.
    """

    requires_shortage_resolution: Literal[True] = True
    shortage_amount: Decimal
    available_strategies: list[str] = ["proportional_winners", "equal_all"]
