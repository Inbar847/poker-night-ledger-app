import uuid

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.participant import Participant, ParticipantStatus, ParticipantType, RoleInGame
from app.models.user import User

# Statuses that are included in settlement calculations and require final stacks.
_SETTLEMENT_ELIGIBLE_STATUSES = (ParticipantStatus.active, ParticipantStatus.left_early)


def get_participant_for_user(
    db: Session, game_id: uuid.UUID, user_id: uuid.UUID
) -> Participant | None:
    return (
        db.query(Participant)
        .filter(Participant.game_id == game_id, Participant.user_id == user_id)
        .first()
    )


def get_participants(db: Session, game_id: uuid.UUID) -> list[Participant]:
    return db.query(Participant).filter(Participant.game_id == game_id).all()


def invite_user(db: Session, game: Game, user: User) -> Participant:
    """Add a registered user as a player. Caller must verify no duplicate."""
    participant = Participant(
        game_id=game.id,
        user_id=user.id,
        participant_type=ParticipantType.registered,
        role_in_game=RoleInGame.player,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def add_guest(db: Session, game: Game, guest_name: str) -> Participant:
    """Add a named guest participant (no user account required)."""
    participant = Participant(
        game_id=game.id,
        guest_name=guest_name,
        participant_type=ParticipantType.guest,
        role_in_game=RoleInGame.player,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def join_by_token(db: Session, game: Game, user: User) -> Participant:
    """Add a registered user as a player via invite token. Caller must verify no duplicate."""
    participant = Participant(
        game_id=game.id,
        user_id=user.id,
        participant_type=ParticipantType.registered,
        role_in_game=RoleInGame.player,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def set_participant_status(
    db: Session, participant_id: uuid.UUID, new_status: ParticipantStatus
) -> Participant:
    """Update a participant's lifecycle status."""
    participant = db.get(Participant, participant_id)
    if participant is None:
        raise ValueError(f"Participant {participant_id} not found")
    participant.status = new_status
    db.commit()
    db.refresh(participant)
    return participant


def get_settlement_eligible_participants(
    db: Session, game_id: uuid.UUID
) -> list[Participant]:
    """Return participants with status active or left_early (included in settlement)."""
    return (
        db.query(Participant)
        .filter(
            Participant.game_id == game_id,
            Participant.status.in_(_SETTLEMENT_ELIGIBLE_STATUSES),
        )
        .all()
    )
