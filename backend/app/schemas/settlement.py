"""
Settlement response schemas for Stage 4.
Shortage resolution fields added post-Phase-2.

Two response shapes:
- SettlementResponse: summary view (balances + transfers)
- SettlementAuditResponse: full audit with per-participant line items
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.ledger import BuyInType


# ---------------------------------------------------------------------------
# Shared transfer
# ---------------------------------------------------------------------------


class Transfer(BaseModel):
    from_participant_id: uuid.UUID
    from_display_name: str
    to_participant_id: uuid.UUID
    to_display_name: str
    amount: Decimal


# ---------------------------------------------------------------------------
# Summary balance (used in SettlementResponse)
# ---------------------------------------------------------------------------


class ParticipantBalance(BaseModel):
    participant_id: uuid.UUID
    display_name: str
    participant_type: str

    # Buy-in side
    total_buy_ins: Decimal

    # Poker side (None if final stack is missing)
    final_chips: Decimal | None
    final_chip_cash_value: Decimal | None
    poker_balance: Decimal | None

    # Expense side
    amount_paid_for_group: Decimal
    owed_expense_share: Decimal
    expense_balance: Decimal

    # Combined (None if final stack is missing)
    net_balance: Decimal | None

    # Shortage resolution (0.00 when no shortage or no final stack)
    shortage_share: Decimal = Decimal("0")
    # adjusted_net_balance = net_balance - shortage_share
    # (None when net_balance is None)
    adjusted_net_balance: Decimal | None = None


class SettlementResponse(BaseModel):
    game_id: uuid.UUID
    game_status: str
    chip_cash_rate: Decimal
    currency: str
    # True when every participant has a final stack
    is_complete: bool
    balances: list[ParticipantBalance]
    # Empty list when is_complete is False
    transfers: list[Transfer]
    # Shortage fields (0 / None when no shortage)
    shortage_amount: Decimal = Decimal("0")
    shortage_strategy: str | None = None


# ---------------------------------------------------------------------------
# Audit line items (used in SettlementAuditResponse)
# ---------------------------------------------------------------------------


class BuyInLineItem(BaseModel):
    buy_in_id: uuid.UUID
    cash_amount: Decimal
    chips_amount: Decimal
    buy_in_type: BuyInType
    created_at: datetime


class ExpensePaidLineItem(BaseModel):
    expense_id: uuid.UUID
    expense_title: str
    total_amount: Decimal


class ExpenseSplitLineItem(BaseModel):
    expense_id: uuid.UUID
    expense_title: str
    share_amount: Decimal


class ParticipantAudit(ParticipantBalance):
    """Extends ParticipantBalance with detailed line items."""

    buy_in_items: list[BuyInLineItem]
    expenses_paid_items: list[ExpensePaidLineItem]
    expense_split_items: list[ExpenseSplitLineItem]


class SettlementAuditResponse(BaseModel):
    game_id: uuid.UUID
    game_status: str
    chip_cash_rate: Decimal
    currency: str
    is_complete: bool
    # Sum of all net_balance values (may differ from 0 by ≤ a few cents due to
    # chip-rate rounding). Included for transparency.
    net_balance_sum: Decimal | None
    participants: list[ParticipantAudit]
    transfers: list[Transfer]
    # Shortage fields (0 / None when no shortage)
    shortage_amount: Decimal = Decimal("0")
    shortage_strategy: str | None = None
