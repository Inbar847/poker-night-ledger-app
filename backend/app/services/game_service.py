import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.participant import Participant, ParticipantType, RoleInGame
from app.schemas.game import GameCreate


def create_game(db: Session, data: GameCreate, creator_user_id: uuid.UUID) -> Game:
    """Create a game and atomically add the creator as the dealer participant."""
    game = Game(
        title=data.title,
        created_by_user_id=creator_user_id,
        dealer_user_id=creator_user_id,
        scheduled_at=data.scheduled_at,
        chip_cash_rate=data.chip_cash_rate,
        currency=data.currency,
        invite_token=secrets.token_urlsafe(32),
    )
    db.add(game)
    db.flush()  # populate game.id before creating the participant

    dealer_participant = Participant(
        game_id=game.id,
        user_id=creator_user_id,
        participant_type=ParticipantType.registered,
        role_in_game=RoleInGame.dealer,
    )
    db.add(dealer_participant)
    db.commit()
    db.refresh(game)
    return game


def get_game_by_id(db: Session, game_id: uuid.UUID) -> Game | None:
    return db.get(Game, game_id)


def get_game_by_invite_token(db: Session, token: str) -> Game | None:
    return db.query(Game).filter(Game.invite_token == token).first()


def list_games_for_user(db: Session, user_id: uuid.UUID) -> list[Game]:
    """Return all non-hidden games where the user has a participant row, newest first."""
    return (
        db.query(Game)
        .join(Participant, Participant.game_id == Game.id)
        .filter(
            Participant.user_id == user_id,
            Participant.hidden_at.is_(None),
        )
        .order_by(Game.created_at.desc())
        .all()
    )


def hide_game_for_user(
    db: Session, game: Game, participant: Participant
) -> Participant:
    """Mark a game as hidden for a specific user by setting hidden_at."""
    if game.status == GameStatus.active:
        raise ValueError("Cannot hide an active game")
    participant.hidden_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(participant)
    return participant


def rotate_invite_token(db: Session, game: Game) -> Game:
    """Generate a new invite token, invalidating the previous one."""
    game.invite_token = secrets.token_urlsafe(32)
    game.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(game)
    return game


def start_game(db: Session, game: Game) -> Game:
    """Transition lobby → active. Raises ValueError if not in lobby."""
    if game.status != GameStatus.lobby:
        raise ValueError(
            f"Game cannot be started from status '{game.status.value}'. "
            "Only a lobby game can be started."
        )
    game.status = GameStatus.active
    game.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(game)
    return game


def close_game(db: Session, game: Game) -> Game:
    """Transition active → closed. Raises ValueError if not active."""
    if game.status != GameStatus.active:
        raise ValueError(
            f"Game cannot be closed from status '{game.status.value}'. "
            "Only an active game can be closed."
        )
    game.status = GameStatus.closed
    game.closed_at = datetime.now(timezone.utc)
    game.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(game)
    return game
