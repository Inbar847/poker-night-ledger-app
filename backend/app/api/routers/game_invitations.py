import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.game import Game, GameStatus
from app.models.participant import Participant, RoleInGame
from app.models.user import User
from app.realtime import events as rt_events
from app.realtime.manager import manager
from app.realtime.personal_manager import personal_manager
from app.schemas.game_invitation import (
    GameInvitationCreate,
    GameInvitationResponse,
)
from app.services import game_invitation_service, participant_service

router = APIRouter(tags=["game_invitations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_game_or_404(db: Session, game_id: uuid.UUID) -> Game:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


def _require_dealer(db: Session, game_id: uuid.UUID, user_id: uuid.UUID) -> Participant:
    p = participant_service.get_participant_for_user(db, game_id, user_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this game",
        )
    if p.role_in_game != RoleInGame.dealer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dealer access required",
        )
    return p


def _invitation_to_response(
    invitation, db: Session
) -> GameInvitationResponse:
    invited_user = db.get(User, invitation.invited_user_id)
    display_name = "Unknown"
    if invited_user:
        display_name = invited_user.full_name or invited_user.email
    return GameInvitationResponse(
        id=invitation.id,
        game_id=invitation.game_id,
        invited_user_id=invitation.invited_user_id,
        invited_user_display_name=display_name,
        invited_by_user_id=invitation.invited_by_user_id,
        status=invitation.status.value,
        created_at=invitation.created_at,
    )


def _build_participant_response(participant: Participant, user: User | None) -> dict:
    """Build a participant dict for realtime broadcast."""
    display_name = participant.guest_name or ""
    if user and user.full_name:
        display_name = user.full_name
    elif user:
        display_name = user.email
    elif not display_name:
        display_name = f"Player ({str(participant.id)[:8]})"

    return {
        "id": str(participant.id),
        "game_id": str(participant.game_id),
        "user_id": str(participant.user_id) if participant.user_id else None,
        "guest_name": participant.guest_name,
        "display_name": display_name,
        "participant_type": participant.participant_type.value,
        "role_in_game": participant.role_in_game.value,
        "status": participant.status.value if participant.status else "active",
        "joined_at": participant.joined_at.isoformat() if participant.joined_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/games/{game_id}/invitations",
    response_model=GameInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    game_id: uuid.UUID,
    body: GameInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GameInvitationResponse:
    game = _get_game_or_404(db, game_id)
    _require_dealer(db, game_id, current_user.id)

    invitation = game_invitation_service.create_invitation(
        db=db,
        game=game,
        invited_user_id=body.invited_user_id,
        invited_by_user_id=current_user.id,
    )

    # Send live popup event to the invited user's personal channel (Stage 26)
    inviter_name = current_user.full_name or current_user.email
    await personal_manager.send_to_user(
        invitation.invited_user_id,
        rt_events.user_game_invitation(
            invitation_id=invitation.id,
            game_id=game.id,
            game_title=game.title,
            inviter_name=inviter_name,
        ),
    )

    return _invitation_to_response(invitation, db)


@router.get(
    "/games/{game_id}/invitations",
    response_model=list[GameInvitationResponse],
)
def list_game_invitations(
    game_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GameInvitationResponse]:
    _get_game_or_404(db, game_id)
    _require_dealer(db, game_id, current_user.id)

    invitations = game_invitation_service.list_pending_for_game(db, game_id)
    return [_invitation_to_response(inv, db) for inv in invitations]


@router.post(
    "/games/{game_id}/invitations/{invitation_id}/accept",
    response_model=GameInvitationResponse,
)
async def accept_invitation(
    game_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GameInvitationResponse:
    invitation, participant = game_invitation_service.accept_invitation(
        db=db,
        invitation_id=invitation_id,
        user_id=current_user.id,
    )

    # Broadcast to game room
    participant_data = _build_participant_response(participant, current_user)
    await manager.broadcast(
        game_id,
        rt_events.invitation_accepted(game_id, participant_data),
    )
    await manager.broadcast(
        game_id,
        rt_events.participant_joined(game_id, participant_data),
    )

    return _invitation_to_response(invitation, db)


@router.post(
    "/games/{game_id}/invitations/{invitation_id}/decline",
    response_model=GameInvitationResponse,
)
def decline_invitation(
    game_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GameInvitationResponse:
    invitation = game_invitation_service.decline_invitation(
        db=db,
        invitation_id=invitation_id,
        user_id=current_user.id,
    )
    return _invitation_to_response(invitation, db)


@router.get(
    "/invitations/pending",
    response_model=list[GameInvitationResponse],
)
def list_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[GameInvitationResponse]:
    invitations = game_invitation_service.list_pending_for_user(db, current_user.id)
    return [_invitation_to_response(inv, db) for inv in invitations]
