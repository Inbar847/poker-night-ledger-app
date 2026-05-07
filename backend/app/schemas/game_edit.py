import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.game_edit import GameEditType


class ClosedGameBuyInCreate(BaseModel):
    participant_id: uuid.UUID
    cash_amount: Decimal = Field(gt=0)
    chips_amount: Decimal = Field(ge=0)
    buy_in_type: str = "initial"


class ClosedGameBuyInUpdate(BaseModel):
    cash_amount: Decimal | None = Field(default=None, gt=0)
    chips_amount: Decimal | None = Field(default=None, ge=0)


class ClosedGameFinalStackUpdate(BaseModel):
    chips_amount: Decimal = Field(ge=0)


class GameEditResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    edited_by_user_id: uuid.UUID
    edited_by_display_name: str
    edit_type: GameEditType
    entity_id: uuid.UUID
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    created_at: datetime
