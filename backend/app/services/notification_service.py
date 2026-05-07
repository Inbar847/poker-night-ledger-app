"""
Notification service — creates and queries persistent in-app notifications.

create_notification: used by friendship_service, games router (invite, start, close).
list/count/mark functions: called by the notifications router (Stage 16).
"""

import uuid
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    data: dict[str, Any] | None = None,
) -> Notification:
    """Append a notification for `user_id`.

    Uses db.flush() rather than db.commit() so the caller controls the
    transaction boundary — the notification is written atomically with the
    record that triggered it.
    """
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        read=False,
        data=data,
    )
    db.add(notification)
    db.flush()
    return notification


def list_notifications(
    db: Session, user_id: uuid.UUID, limit: int = 50
) -> list[Notification]:
    """Return up to `limit` notifications for a user, newest-first."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    """Return the number of unread notifications for a user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .count()
    )


def mark_read(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification | None:
    """Mark a single notification as read.

    Returns None if the notification does not exist or belongs to a different user.
    """
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        return None
    if not n.read:
        n.read = True
        db.commit()
        db.refresh(n)
    return n


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    """Mark all unread notifications as read. Returns count of rows updated."""
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .update({"read": True}, synchronize_session="fetch")
    )
    db.commit()
    return updated


def delete_all_for_user(db: Session, user_id: uuid.UUID) -> int:
    """Permanently delete all notifications for a user. Returns count of rows deleted."""
    deleted = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .delete(synchronize_session="fetch")
    )
    db.commit()
    return deleted


def delete_settlement_owed_for_game(db: Session, game_id: uuid.UUID) -> int:
    """Delete all settlement_owed notifications for a specific game.

    Matches by data->>'game_id'. Uses Python-level filtering for SQLite
    compatibility in tests.

    Uses flush() instead of commit() so the caller controls the transaction.
    """
    game_id_str = str(game_id)
    notifications = (
        db.query(Notification)
        .filter(Notification.type == NotificationType.settlement_owed)
        .all()
    )
    count = 0
    for n in notifications:
        if n.data and n.data.get("game_id") == game_id_str:
            db.delete(n)
            count += 1
    if count:
        db.flush()
    return count
