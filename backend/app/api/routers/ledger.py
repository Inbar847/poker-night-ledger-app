"""
Ledger router — buy-ins, expenses, and final stacks for a live game.

Buy-in mutation endpoints are dealer-only.
Expense mutations: any active participant can create (self as payer);
creator or dealer can edit/delete.
All read endpoints require game participation.

Stage 5: mutation endpoints are async so they can await manager.broadcast().
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.game import Game
from app.models.participant import Participant, ParticipantStatus, RoleInGame
from app.models.user import User
from app.realtime import events as rt_events
from app.realtime.manager import manager
from app.schemas.ledger import (
    BuyInCreate,
    BuyInResponse,
    BuyInUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    FinalStackResponse,
    FinalStackUpsert,
)
from app.services import game_service, ledger_service, participant_service

router = APIRouter(prefix="/games", tags=["ledger"])


# ---------------------------------------------------------------------------
# Shared helpers (mirrors pattern from games.py to keep routers thin)
# ---------------------------------------------------------------------------


def _get_game_or_404(db: Session, game_id: uuid.UUID) -> Game:
    game = game_service.get_game_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


def _get_participant_or_403(db: Session, game_id: uuid.UUID, user_id: uuid.UUID) -> Participant:
    p = participant_service.get_participant_for_user(db, game_id, user_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this game",
        )
    return p


def _require_dealer(participant: Participant) -> None:
    if participant.role_in_game != RoleInGame.dealer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealer access required",
        )


def _service_error_to_http(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ---------------------------------------------------------------------------
# Buy-ins
# ---------------------------------------------------------------------------


@router.post(
    "/{game_id}/buy-ins",
    response_model=BuyInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_buy_in(
    game_id: uuid.UUID,
    data: BuyInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyInResponse:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)
    try:
        result = ledger_service.create_buy_in(db, game, data, current_user.id)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    buy_in_data = BuyInResponse.model_validate(result).model_dump(mode="json")
    await manager.broadcast(game_id, rt_events.buyin_created(game_id, buy_in_data))
    return result


@router.get("/{game_id}/buy-ins", response_model=list[BuyInResponse])
def list_buy_ins(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BuyInResponse]:
    _get_game_or_404(db, game_id)
    _get_participant_or_403(db, game_id, current_user.id)
    return ledger_service.list_buy_ins(db, game_id)


@router.patch("/{game_id}/buy-ins/{buy_in_id}", response_model=BuyInResponse)
async def update_buy_in(
    game_id: uuid.UUID,
    buy_in_id: uuid.UUID,
    data: BuyInUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BuyInResponse:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    buy_in = ledger_service.get_buy_in(db, game_id, buy_in_id)
    if buy_in is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buy-in not found")

    try:
        result = ledger_service.update_buy_in(db, game, buy_in, data)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    buy_in_data = BuyInResponse.model_validate(result).model_dump(mode="json")
    await manager.broadcast(game_id, rt_events.buyin_updated(game_id, buy_in_data))
    return result


@router.delete("/{game_id}/buy-ins/{buy_in_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_buy_in(
    game_id: uuid.UUID,
    buy_in_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(participant)

    buy_in = ledger_service.get_buy_in(db, game_id, buy_in_id)
    if buy_in is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buy-in not found")

    deleted_id = buy_in.id
    try:
        ledger_service.delete_buy_in(db, game, buy_in)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    await manager.broadcast(game_id, rt_events.buyin_deleted(game_id, deleted_id))


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


@router.post(
    "/{game_id}/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    game_id: uuid.UUID,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)

    # Any active participant can create an expense (not just dealer).
    # left_early and removed_before_start are blocked.
    if participant.status != ParticipantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active participants can create expenses",
        )

    # Non-dealer participants must be the payer (cannot claim someone else paid).
    if (
        participant.role_in_game != RoleInGame.dealer
        and data.paid_by_participant_id != participant.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non-dealer participants can only create expenses where they are the payer",
        )

    try:
        result = ledger_service.create_expense(db, game, data, current_user.id)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    expense_data = ExpenseResponse.model_validate(result).model_dump(mode="json")
    await manager.broadcast(game_id, rt_events.expense_created(game_id, expense_data))
    return result


@router.get("/{game_id}/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExpenseResponse]:
    _get_game_or_404(db, game_id)
    _get_participant_or_403(db, game_id, current_user.id)
    return ledger_service.list_expenses(db, game_id)


@router.patch("/{game_id}/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    game_id: uuid.UUID,
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseResponse:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)

    expense = ledger_service.get_expense(db, game_id, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Allow update if caller is the dealer OR the expense creator.
    is_dealer = participant.role_in_game == RoleInGame.dealer
    is_creator = expense.created_by_user_id == current_user.id
    if not is_dealer and not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the dealer or expense creator can edit this expense",
        )

    # If the caller is not the dealer and is changing paid_by, it must remain their own.
    if (
        not is_dealer
        and data.paid_by_participant_id is not None
        and data.paid_by_participant_id != participant.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non-dealer participants can only set themselves as payer",
        )

    try:
        result = ledger_service.update_expense(db, game, expense, data)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    expense_data = ExpenseResponse.model_validate(result).model_dump(mode="json")
    await manager.broadcast(game_id, rt_events.expense_updated(game_id, expense_data))
    return result


@router.delete("/{game_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    game_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    game = _get_game_or_404(db, game_id)
    participant = _get_participant_or_403(db, game_id, current_user.id)

    expense = ledger_service.get_expense(db, game_id, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Allow delete if caller is the dealer OR the expense creator.
    is_dealer = participant.role_in_game == RoleInGame.dealer
    is_creator = expense.created_by_user_id == current_user.id
    if not is_dealer and not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the dealer or expense creator can delete this expense",
        )

    deleted_id = expense.id
    try:
        ledger_service.delete_expense(db, game, expense)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    await manager.broadcast(game_id, rt_events.expense_deleted(game_id, deleted_id))


# ---------------------------------------------------------------------------
# Final stacks
# ---------------------------------------------------------------------------


@router.put(
    "/{game_id}/final-stacks/{participant_id}",
    response_model=FinalStackResponse,
)
async def upsert_final_stack(
    game_id: uuid.UUID,
    participant_id: uuid.UUID,
    data: FinalStackUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinalStackResponse:
    game = _get_game_or_404(db, game_id)
    requester = _get_participant_or_403(db, game_id, current_user.id)
    _require_dealer(requester)
    try:
        result = ledger_service.upsert_final_stack(db, game, participant_id, data)
    except ValueError as exc:
        raise _service_error_to_http(exc) from exc
    stack_data = FinalStackResponse.model_validate(result).model_dump(mode="json")
    await manager.broadcast(game_id, rt_events.final_stack_updated(game_id, stack_data))
    return result


@router.get("/{game_id}/final-stacks", response_model=list[FinalStackResponse])
def list_final_stacks(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FinalStackResponse]:
    _get_game_or_404(db, game_id)
    _get_participant_or_403(db, game_id, current_user.id)
    return ledger_service.list_final_stacks(db, game_id)
