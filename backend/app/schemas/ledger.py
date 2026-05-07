import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.ledger import BuyInType


# ---------------------------------------------------------------------------
# Buy-in schemas
# ---------------------------------------------------------------------------


class BuyInCreate(BaseModel):
    participant_id: uuid.UUID
    cash_amount: Decimal = Field(gt=0)
    chips_amount: Decimal = Field(ge=0)
    buy_in_type: BuyInType = BuyInType.initial


class BuyInUpdate(BaseModel):
    cash_amount: Decimal | None = Field(default=None, gt=0)
    chips_amount: Decimal | None = Field(default=None, ge=0)
    buy_in_type: BuyInType | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "BuyInUpdate":
        if self.cash_amount is None and self.chips_amount is None and self.buy_in_type is None:
            raise ValueError(
                "At least one field must be provided for a buy-in update "
                "(cash_amount, chips_amount, or buy_in_type)."
            )
        return self


class BuyInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    participant_id: uuid.UUID
    cash_amount: Decimal
    chips_amount: Decimal
    buy_in_type: BuyInType
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Expense schemas
# ---------------------------------------------------------------------------


class ExpenseSplitInput(BaseModel):
    participant_id: uuid.UUID
    share_amount: Decimal = Field(gt=0)


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    total_amount: Decimal = Field(gt=0)
    paid_by_participant_id: uuid.UUID
    splits: list[ExpenseSplitInput] = Field(min_length=1)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank or whitespace-only.")
        return stripped

    @model_validator(mode="after")
    def splits_sum_to_total(self) -> "ExpenseCreate":
        split_sum = sum(s.share_amount for s in self.splits)
        # Allow up to 1 cent of rounding tolerance
        if abs(split_sum - self.total_amount) > Decimal("0.01"):
            raise ValueError(
                f"Split amounts sum to {split_sum} but total_amount is {self.total_amount}"
            )
        return self


class ExpenseSplitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    expense_id: uuid.UUID
    participant_id: uuid.UUID
    share_amount: Decimal


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    title: str
    total_amount: Decimal
    paid_by_participant_id: uuid.UUID
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    splits: list[ExpenseSplitResponse] = []


class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    total_amount: Decimal | None = Field(default=None, gt=0)
    paid_by_participant_id: uuid.UUID | None = None
    splits: list[ExpenseSplitInput] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("title must not be blank or whitespace-only.")
        return stripped

    @model_validator(mode="after")
    def splits_match_total_if_both_given(self) -> "ExpenseUpdate":
        if self.splits is not None and self.total_amount is not None:
            split_sum = sum(s.share_amount for s in self.splits)
            if abs(split_sum - self.total_amount) > Decimal("0.01"):
                raise ValueError(
                    f"Split amounts sum to {split_sum} but total_amount is {self.total_amount}"
                )
        return self


# ---------------------------------------------------------------------------
# Final stack schemas
# ---------------------------------------------------------------------------


class FinalStackUpsert(BaseModel):
    chips_amount: Decimal = Field(ge=0)


class FinalStackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    participant_id: uuid.UUID
    chips_amount: Decimal
    created_at: datetime
    updated_at: datetime
