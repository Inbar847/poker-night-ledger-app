"""
Early cash-out service — Stage 20.

Allows a player to leave an active game early by recording their own final
chip count and transitioning their participant status to left_early.

Business rules:
- Game must be active.
- Caller must be the participant themselves (user_id matches).
- Participant status must be 'active' (cannot re-cashout or cashout if removed).
- Creates or updates a final_stacks row for the participant.
- Sets participant status to 'left_early'.
- Dealer retains the ability to edit the cash-out value via the existing
  PUT /games/{id}/final-stacks/{pid} endpoint (dealer-only).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.ledger import FinalStack
from app.models.participant import Participant, ParticipantStatus


def cashout(
    db: Session,
    game: Game,
    participant: Participant,
    chips_amount: Decimal,
    caller_user_id: uuid.UUID,
) -> FinalStack:
    """Process an early cash-out for a player.

    Returns the created/updated FinalStack row.
    Raises ValueError on validation failure.
    """
    # Game must be active
    if game.status != GameStatus.active:
        raise ValueError(
            f"Game is not active (current status: {game.status.value}). "
            "Early cash-out is only available during an active game."
        )

    # Caller must be the participant themselves
    if participant.user_id is None or participant.user_id != caller_user_id:
        raise ValueError("Only the player themselves can initiate early cash-out.")

    # Participant must be active
    if participant.status != ParticipantStatus.active:
        raise ValueError(
            f"Participant status is '{participant.status.value}'. "
            "Only active participants can cash out early."
        )

    # Create or update the final stack record
    existing = (
        db.query(FinalStack)
        .filter(
            FinalStack.game_id == game.id,
            FinalStack.participant_id == participant.id,
        )
        .first()
    )

    if existing:
        existing.chips_amount = chips_amount
        existing.updated_at = datetime.now(timezone.utc)
        final_stack = existing
    else:
        final_stack = FinalStack(
            game_id=game.id,
            participant_id=participant.id,
            chips_amount=chips_amount,
        )
        db.add(final_stack)

    # Transition participant status to left_early
    participant.status = ParticipantStatus.left_early

    db.commit()
    db.refresh(final_stack)
    db.refresh(participant)
    return final_stack
