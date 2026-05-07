"""Notifications router — list, unread count, and mark-read endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    return notification_service.list_notifications(db, current_user.id)


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    count = notification_service.get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/read-all", response_model=MarkAllReadResponse)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkAllReadResponse:
    marked = notification_service.mark_all_read(db, current_user.id)
    return MarkAllReadResponse(marked_read=marked)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    notification_service.delete_all_for_user(db, current_user.id)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    n = notification_service.mark_read(db, notification_id, current_user.id)
    if n is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return n
