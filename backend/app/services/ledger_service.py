"""
Core live-game ledger service.

Business rules enforced here:
- Buy-ins and expenses require the game to be in 'active' status.
- Final stacks also require 'active' status.
- Dealer-only checks are enforced in the router; this layer trusts the caller.
- Expense splits must be supplied by the caller and are validated at the schema
  level (splits sum ≈ total_amount). This service re-validates before writing,
  and additionally rejects duplicate participant_ids within the same splits list.
- Final stacks are upserted: one row per participant per game.

Game status transitions (start / close) live in game_service, not here.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.ledger import BuyIn, Expense, ExpenseSplit, FinalStack
from app.models.participant import Participant, ParticipantStatus
from app.schemas.ledger import (
    BuyInCreate,
    BuyInUpdate,
    ExpenseCreate,
    ExpenseSplitInput,
    ExpenseUpdate,
    FinalStackUpsert,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_active(game: Game) -> None:
    if game.status != GameStatus.active:
        raise ValueError(
            f"Game is not active (current status: {game.status.value}). "
            "Ledger changes are only allowed during an active game."
        )


def _get_participant_in_game(
    db: Session, game_id: uuid.UUID, participant_id: uuid.UUID
) -> Participant | None:
    return (
        db.query(Participant)
        .filter(
            Participant.id == participant_id,
            Participant.game_id == game_id,
        )
        .first()
    )


def _validate_splits(
    db: Session, game_id: uuid.UUID, splits: list[ExpenseSplitInput], total_amount: Decimal
) -> None:
    """Validate splits: no duplicates, all participants in game, sum ≈ total_amount."""
    participant_ids = [s.participant_id for s in splits]
    if len(participant_ids) != len(set(participant_ids)):
        raise ValueError(
            "Splits list contains duplicate participant_id values. "
            "Each participant may appear at most once per expense."
        )

    split_sum = Decimal(0)
    for s in splits:
        p = _get_participant_in_game(db, game_id, s.participant_id)
        if p is None:
            raise ValueError(
                f"Participant {s.participant_id} does not belong to game {game_id}"
            )
        split_sum += s.share_amount

    if abs(split_sum - total_amount) > Decimal("0.01"):
        raise ValueError(
            f"Expense splits sum to {split_sum} but total_amount is {total_amount}"
        )


# ---------------------------------------------------------------------------
# Buy-ins
# ---------------------------------------------------------------------------


def create_buy_in(
    db: Session, game: Game, data: BuyInCreate, created_by_user_id: uuid.UUID
) -> BuyIn:
    _require_active(game)

    participant = _get_participant_in_game(db, game.id, data.participant_id)
    if participant is None:
        raise ValueError(
            f"Participant {data.participant_id} does not belong to game {game.id}"
        )

    if participant.status == ParticipantStatus.left_early:
        raise ValueError(
            "Cannot add a buy-in for a participant who has left early."
        )

    buy_in = BuyIn(
        game_id=game.id,
        participant_id=data.participant_id,
        cash_amount=data.cash_amount,
        chips_amount=data.chips_amount,
        buy_in_type=data.buy_in_type,
        created_by_user_id=created_by_user_id,
    )
    db.add(buy_in)
    db.commit()
    db.refresh(buy_in)
    return buy_in


def list_buy_ins(db: Session, game_id: uuid.UUID) -> list[BuyIn]:
    return (
        db.query(BuyIn)
        .filter(BuyIn.game_id == game_id)
        .order_by(BuyIn.created_at)
        .all()
    )


def get_buy_in(db: Session, game_id: uuid.UUID, buy_in_id: uuid.UUID) -> BuyIn | None:
    return (
        db.query(BuyIn)
        .filter(BuyIn.id == buy_in_id, BuyIn.game_id == game_id)
        .first()
    )


def update_buy_in(db: Session, game: Game, buy_in: BuyIn, data: BuyInUpdate) -> BuyIn:
    _require_active(game)

    if data.cash_amount is not None:
        buy_in.cash_amount = data.cash_amount
    if data.chips_amount is not None:
        buy_in.chips_amount = data.chips_amount
    if data.buy_in_type is not None:
        buy_in.buy_in_type = data.buy_in_type

    buy_in.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(buy_in)
    return buy_in


def delete_buy_in(db: Session, game: Game, buy_in: BuyIn) -> None:
    _require_active(game)
    db.delete(buy_in)
    db.commit()


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


def create_expense(
    db: Session, game: Game, data: ExpenseCreate, created_by_user_id: uuid.UUID
) -> Expense:
    _require_active(game)

    # Validate paid_by participant belongs to this game
    payer = _get_participant_in_game(db, game.id, data.paid_by_participant_id)
    if payer is None:
        raise ValueError(
            f"Participant {data.paid_by_participant_id} does not belong to game {game.id}"
        )

    _validate_splits(db, game.id, data.splits, data.total_amount)

    expense = Expense(
        game_id=game.id,
        title=data.title,
        total_amount=data.total_amount,
        paid_by_participant_id=data.paid_by_participant_id,
        created_by_user_id=created_by_user_id,
    )
    db.add(expense)
    db.flush()  # populate expense.id before creating splits

    for split_input in data.splits:
        db.add(
            ExpenseSplit(
                expense_id=expense.id,
                participant_id=split_input.participant_id,
                share_amount=split_input.share_amount,
            )
        )

    db.commit()
    db.refresh(expense)
    expense.splits  # noqa: B018 — trigger lazy load while session is open
    return expense


def list_expenses(db: Session, game_id: uuid.UUID) -> list[Expense]:
    expenses = (
        db.query(Expense)
        .filter(Expense.game_id == game_id)
        .order_by(Expense.created_at)
        .all()
    )
    for e in expenses:
        e.splits  # noqa: B018 — trigger lazy load while session is open
    return expenses


def get_expense(db: Session, game_id: uuid.UUID, expense_id: uuid.UUID) -> Expense | None:
    return (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.game_id == game_id)
        .first()
    )


def update_expense(
    db: Session, game: Game, expense: Expense, data: ExpenseUpdate
) -> Expense:
    _require_active(game)

    new_total = data.total_amount if data.total_amount is not None else expense.total_amount
    new_splits = data.splits

    if new_splits is not None:
        _validate_splits(db, game.id, new_splits, new_total)

    if data.title is not None:
        expense.title = data.title
    if data.total_amount is not None:
        expense.total_amount = data.total_amount
    if data.paid_by_participant_id is not None:
        payer = _get_participant_in_game(db, game.id, data.paid_by_participant_id)
        if payer is None:
            raise ValueError(
                f"Participant {data.paid_by_participant_id} does not belong to game {game.id}"
            )
        expense.paid_by_participant_id = data.paid_by_participant_id

    if new_splits is not None:
        # Replace splits: delete old rows, insert new ones.
        # The manual delete is intentional here — we are replacing the collection,
        # not deleting the parent, so we cannot rely on cascade="delete-orphan"
        # to fire automatically without an explicit flush cycle.
        db.query(ExpenseSplit).filter(ExpenseSplit.expense_id == expense.id).delete()
        for split_input in new_splits:
            db.add(
                ExpenseSplit(
                    expense_id=expense.id,
                    participant_id=split_input.participant_id,
                    share_amount=split_input.share_amount,
                )
            )

    expense.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(expense)
    expense.splits  # noqa: B018 — trigger lazy load while session is open
    return expense


def delete_expense(db: Session, game: Game, expense: Expense) -> None:
    """Delete an expense and its splits.

    Split deletion is handled by the ORM cascade="all, delete-orphan" defined
    on Expense.splits. We do NOT manually delete ExpenseSplit rows here — doing
    so before db.delete(expense) would create a conflict between the manual
    delete and the cascade on PostgreSQL (the ORM may attempt a second delete
    for already-removed rows that it tracked in the identity map).
    """
    _require_active(game)
    db.delete(expense)
    db.commit()


# ---------------------------------------------------------------------------
# Final stacks
# ---------------------------------------------------------------------------


def upsert_final_stack(
    db: Session, game: Game, participant_id: uuid.UUID, data: FinalStackUpsert
) -> FinalStack:
    _require_active(game)

    participant = _get_participant_in_game(db, game.id, participant_id)
    if participant is None:
        raise ValueError(
            f"Participant {participant_id} does not belong to game {game.id}"
        )

    existing = (
        db.query(FinalStack)
        .filter(
            FinalStack.game_id == game.id,
            FinalStack.participant_id == participant_id,
        )
        .first()
    )

    if existing:
        existing.chips_amount = data.chips_amount
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    stack = FinalStack(
        game_id=game.id,
        participant_id=participant_id,
        chips_amount=data.chips_amount,
    )
    db.add(stack)
    db.commit()
    db.refresh(stack)
    return stack


def list_final_stacks(db: Session, game_id: uuid.UUID) -> list[FinalStack]:
    return (
        db.query(FinalStack)
        .filter(FinalStack.game_id == game_id)
        .order_by(FinalStack.created_at)
        .all()
    )
