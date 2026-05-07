"""
Game invitation service — business logic for the pending invitation flow.

Dealers invite accepted friends to a game. The invitation is pending until the
invited user accepts or declines. Only acceptance creates a participant record.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.game_invitation import GameInvitation, GameInvitationStatus
from app.models.notification import NotificationType
from app.models.participant import Participant, ParticipantType, RoleInGame
from app.models.user import User
from app.services import friendship_service, notification_service


def create_invitation(
    db: Session,
    game: Game,
    invited_user_id: uuid.UUID,
    invited_by_user_id: uuid.UUID,
) -> GameInvitation:
    """Create a pending game invitation.

    Validates:
    - Game is not closed
    - Invited user exists
    - Invited user is an accepted friend of the dealer
    - No existing pending/accepted invitation for this user+game
    - User is not already a participant
    """
    if game.status == GameStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite to a closed game",
        )

    invited_user = db.get(User, invited_user_id)
    if invited_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not friendship_service.are_friends(db, invited_by_user_id, invited_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only invite accepted friends",
        )

    # Check for existing invitation (any status)
    existing = (
        db.query(GameInvitation)
        .filter(
            GameInvitation.game_id == game.id,
            GameInvitation.invited_user_id == invited_user_id,
            GameInvitation.status.in_([
                GameInvitationStatus.pending,
                GameInvitationStatus.accepted,
            ]),
        )
        .first()
    )
    if existing is not None:
        if existing.status == GameInvitationStatus.accepted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User has already accepted an invitation to this game",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation already exists for this user",
        )

    # Check if user is already a participant
    already_participant = (
        db.query(Participant)
        .filter(
            Participant.game_id == game.id,
            Participant.user_id == invited_user_id,
        )
        .first()
    )
    if already_participant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a participant in this game",
        )

    invitation = GameInvitation(
        game_id=game.id,
        invited_user_id=invited_user_id,
        invited_by_user_id=invited_by_user_id,
        status=GameInvitationStatus.pending,
    )
    db.add(invitation)
    db.flush()

    # Create notification for the invited user
    notification_service.create_notification(
        db=db,
        user_id=invited_user_id,
        notification_type=NotificationType.game_invitation,
        data={
            "game_id": str(game.id),
            "game_title": game.title,
            "invitation_id": str(invitation.id),
            "invited_by_user_id": str(invited_by_user_id),
        },
    )

    db.commit()
    db.refresh(invitation)
    return invitation


def accept_invitation(
    db: Session,
    invitation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[GameInvitation, Participant]:
    """Accept a pending invitation and create a participant record.

    Returns the updated invitation and the new participant.
    """
    invitation = db.get(GameInvitation, invitation_id)
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.invited_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the invited user can accept this invitation",
        )

    if invitation.status != GameInvitationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is not pending (current status: {invitation.status})",
        )

    # Check the game isn't closed
    game = db.get(Game, invitation.game_id)
    if game is not None and game.status == GameStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join a closed game",
        )

    # Guard against race condition: user might already be a participant
    existing_participant = (
        db.query(Participant)
        .filter(
            Participant.game_id == invitation.game_id,
            Participant.user_id == user_id,
        )
        .first()
    )
    if existing_participant is not None:
        invitation.status = GameInvitationStatus.accepted
        db.commit()
        db.refresh(invitation)
        return invitation, existing_participant

    # Create participant
    participant = Participant(
        game_id=invitation.game_id,
        user_id=user_id,
        participant_type=ParticipantType.registered,
        role_in_game=RoleInGame.player,
    )
    db.add(participant)

    invitation.status = GameInvitationStatus.accepted
    db.commit()
    db.refresh(invitation)
    db.refresh(participant)
    return invitation, participant


def decline_invitation(
    db: Session,
    invitation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> GameInvitation:
    """Decline a pending invitation."""
    invitation = db.get(GameInvitation, invitation_id)
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.invited_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the invited user can decline this invitation",
        )

    if invitation.status != GameInvitationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is not pending (current status: {invitation.status})",
        )

    invitation.status = GameInvitationStatus.declined
    db.commit()
    db.refresh(invitation)
    return invitation


def list_pending_for_game(db: Session, game_id: uuid.UUID) -> list[GameInvitation]:
    """List pending invitations for a game (dealer's lobby view)."""
    return (
        db.query(GameInvitation)
        .filter(
            GameInvitation.game_id == game_id,
            GameInvitation.status == GameInvitationStatus.pending,
        )
        .all()
    )


def list_pending_for_user(db: Session, user_id: uuid.UUID) -> list[GameInvitation]:
    """List pending invitations for a user."""
    return (
        db.query(GameInvitation)
        .filter(
            GameInvitation.invited_user_id == user_id,
            GameInvitation.status == GameInvitationStatus.pending,
        )
        .all()
    )
