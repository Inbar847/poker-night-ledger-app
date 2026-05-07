"""
Game edit service — retroactive editing of closed games (Stage 28).

Handles:
- Edit/create/delete buy-ins on closed games
- Edit final stacks on closed games
- Audit trail recording (before/after snapshots)
- Re-settlement downstream effects after every edit
"""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.game_edit import GameEdit, GameEditType
from app.models.ledger import BuyIn, BuyInType, FinalStack
from app.models.notification import NotificationType
from app.models.participant import Participant
from app.schemas.game_edit import (
    ClosedGameBuyInCreate,
    ClosedGameBuyInUpdate,
    ClosedGameFinalStackUpdate,
)
from app.services import notification_service, participant_service, settlement_service


# ---------------------------------------------------------------------------
# Audit trail helpers
# ---------------------------------------------------------------------------


def _buyin_snapshot(buyin: BuyIn) -> dict:
    """Create a JSON-serializable snapshot of a buy-in record."""
    return {
        "participant_id": str(buyin.participant_id),
        "cash_amount": str(buyin.cash_amount),
        "chips_amount": str(buyin.chips_amount),
        "buy_in_type": buyin.buy_in_type.value if isinstance(buyin.buy_in_type, BuyInType) else buyin.buy_in_type,
    }


def _final_stack_snapshot(fs: FinalStack) -> dict:
    """Create a JSON-serializable snapshot of a final stack record."""
    return {
        "participant_id": str(fs.participant_id),
        "chips_amount": str(fs.chips_amount),
    }


def _record_edit(
    db: Session,
    game_id: uuid.UUID,
    edited_by_user_id: uuid.UUID,
    edit_type: GameEditType,
    entity_id: uuid.UUID,
    before_data: dict | None,
    after_data: dict | None,
) -> GameEdit:
    """Create an append-only audit trail entry."""
    edit = GameEdit(
        game_id=game_id,
        edited_by_user_id=edited_by_user_id,
        edit_type=edit_type,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
    )
    db.add(edit)
    db.flush()
    return edit


# ---------------------------------------------------------------------------
# Re-settlement downstream effects
# ---------------------------------------------------------------------------


def _trigger_resettlement(db: Session, game: Game) -> None:
    """Execute all downstream effects after a retroactive edit.

    1. Delete stale settlement_owed notifications for this game
    2. Recompute settlement (updates shortage fields on game)
    3. Create new settlement_owed notifications for updated debtors
    4. Create game_resettled notification for all registered participants
    """
    # 1. Delete stale settlement_owed notifications
    notification_service.delete_settlement_owed_for_game(db, game.id)

    # 2. Recompute settlement
    settlement = settlement_service.resettle_game(db, game)

    # 3. Load participants for notification creation
    participants = participant_service.get_participants(db, game.id)
    pid_to_user: dict[uuid.UUID, uuid.UUID] = {
        p.id: p.user_id for p in participants if p.user_id is not None
    }

    # 4. Create new settlement_owed notifications for debtors
    if settlement.is_complete:
        for transfer in settlement.transfers:
            debtor_user_id = pid_to_user.get(transfer.from_participant_id)
            if debtor_user_id is not None:
                notification_service.create_notification(
                    db,
                    user_id=debtor_user_id,
                    notification_type=NotificationType.settlement_owed,
                    data={
                        "game_id": str(game.id),
                        "game_title": game.title,
                        "to_display_name": transfer.to_display_name,
                        "amount": str(transfer.amount),
                        "currency": game.currency,
                    },
                )

    # 5. Create game_resettled notification for all registered participants
    for p in participants:
        if p.user_id is not None:
            notification_service.create_notification(
                db,
                user_id=p.user_id,
                notification_type=NotificationType.game_resettled,
                data={
                    "game_id": str(game.id),
                    "game_title": game.title,
                },
            )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_closed_game(game: Game) -> None:
    """Raise ValueError if the game is not closed."""
    if game.status != GameStatus.closed:
        raise ValueError("Retroactive editing is only allowed on closed games")


def _validate_participant_in_game(
    db: Session, game_id: uuid.UUID, participant_id: uuid.UUID
) -> Participant:
    """Raise ValueError if the participant does not belong to the game."""
    participant = (
        db.query(Participant)
        .filter(
            Participant.id == participant_id,
            Participant.game_id == game_id,
        )
        .first()
    )
    if participant is None:
        raise ValueError("Participant does not belong to this game")
    return participant


# ---------------------------------------------------------------------------
# Public API — closed-game buy-in operations
# ---------------------------------------------------------------------------


def create_closed_game_buyin(
    db: Session,
    game: Game,
    data: ClosedGameBuyInCreate,
    editor_user_id: uuid.UUID,
) -> BuyIn:
    """Add a new buy-in to a closed game with audit trail and re-settlement."""
    _validate_closed_game(game)
    _validate_participant_in_game(db, game.id, data.participant_id)

    buyin = BuyIn(
        game_id=game.id,
        participant_id=data.participant_id,
        cash_amount=data.cash_amount,
        chips_amount=data.chips_amount,
        buy_in_type=BuyInType(data.buy_in_type),
        created_by_user_id=editor_user_id,
    )
    db.add(buyin)
    db.flush()

    _record_edit(
        db,
        game_id=game.id,
        edited_by_user_id=editor_user_id,
        edit_type=GameEditType.buyin_created,
        entity_id=buyin.id,
        before_data=None,
        after_data=_buyin_snapshot(buyin),
    )

    _trigger_resettlement(db, game)
    db.commit()
    return buyin


def edit_closed_game_buyin(
    db: Session,
    game: Game,
    buyin_id: uuid.UUID,
    data: ClosedGameBuyInUpdate,
    editor_user_id: uuid.UUID,
) -> BuyIn:
    """Edit an existing buy-in on a closed game with audit trail and re-settlement."""
    _validate_closed_game(game)

    buyin = (
        db.query(BuyIn)
        .filter(BuyIn.id == buyin_id, BuyIn.game_id == game.id)
        .first()
    )
    if buyin is None:
        raise ValueError("Buy-in not found in this game")

    before = _buyin_snapshot(buyin)

    if data.cash_amount is not None:
        buyin.cash_amount = data.cash_amount
    if data.chips_amount is not None:
        buyin.chips_amount = data.chips_amount
    db.flush()

    after = _buyin_snapshot(buyin)

    _record_edit(
        db,
        game_id=game.id,
        edited_by_user_id=editor_user_id,
        edit_type=GameEditType.buyin_updated,
        entity_id=buyin.id,
        before_data=before,
        after_data=after,
    )

    _trigger_resettlement(db, game)
    db.commit()
    return buyin


def delete_closed_game_buyin(
    db: Session,
    game: Game,
    buyin_id: uuid.UUID,
    editor_user_id: uuid.UUID,
) -> None:
    """Delete a buy-in from a closed game with audit trail and re-settlement."""
    _validate_closed_game(game)

    buyin = (
        db.query(BuyIn)
        .filter(BuyIn.id == buyin_id, BuyIn.game_id == game.id)
        .first()
    )
    if buyin is None:
        raise ValueError("Buy-in not found in this game")

    before = _buyin_snapshot(buyin)

    _record_edit(
        db,
        game_id=game.id,
        edited_by_user_id=editor_user_id,
        edit_type=GameEditType.buyin_deleted,
        entity_id=buyin.id,
        before_data=before,
        after_data=None,
    )

    db.delete(buyin)
    db.flush()

    _trigger_resettlement(db, game)
    db.commit()


# ---------------------------------------------------------------------------
# Public API — closed-game final stack operations
# ---------------------------------------------------------------------------


def edit_closed_game_final_stack(
    db: Session,
    game: Game,
    participant_id: uuid.UUID,
    data: ClosedGameFinalStackUpdate,
    editor_user_id: uuid.UUID,
) -> FinalStack:
    """Edit a final stack on a closed game with audit trail and re-settlement."""
    _validate_closed_game(game)

    fs = (
        db.query(FinalStack)
        .filter(
            FinalStack.game_id == game.id,
            FinalStack.participant_id == participant_id,
        )
        .first()
    )
    if fs is None:
        raise ValueError("Final stack not found for this participant in this game")

    before = _final_stack_snapshot(fs)

    fs.chips_amount = data.chips_amount
    db.flush()

    after = _final_stack_snapshot(fs)

    _record_edit(
        db,
        game_id=game.id,
        edited_by_user_id=editor_user_id,
        edit_type=GameEditType.final_stack_updated,
        entity_id=fs.id,
        before_data=before,
        after_data=after,
    )

    _trigger_resettlement(db, game)
    db.commit()
    return fs


# ---------------------------------------------------------------------------
# Public API — audit trail
# ---------------------------------------------------------------------------


def list_edits_for_game(db: Session, game_id: uuid.UUID) -> list[GameEdit]:
    """Return all audit trail entries for a game, ordered by created_at ascending."""
    return (
        db.query(GameEdit)
        .filter(GameEdit.game_id == game_id)
        .order_by(GameEdit.created_at)
        .all()
    )
