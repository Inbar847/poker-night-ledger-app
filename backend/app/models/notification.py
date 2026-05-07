import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database.session import Base


class NotificationType(str, enum.Enum):
    friend_request_received = "friend_request_received"
    friend_request_accepted = "friend_request_accepted"
    game_invitation = "game_invitation"
    game_started = "game_started"
    game_closed = "game_closed"
    settlement_owed = "settlement_owed"
    game_resettled = "game_resettled"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, native_enum=False, length=32),
        nullable=False,
    )
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # JSONB in Postgres; stored as text in SQLite for tests
    data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # Primary read path: all notifications for a user, unread-first
        Index("ix_notifications_user_read_created", "user_id", "read", "created_at"),
    )
