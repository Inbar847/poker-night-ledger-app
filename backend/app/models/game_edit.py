import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database.session import Base


class GameEditType(str, enum.Enum):
    buyin_created = "buyin_created"
    buyin_updated = "buyin_updated"
    buyin_deleted = "buyin_deleted"
    final_stack_updated = "final_stack_updated"


class GameEdit(Base):
    __tablename__ = "game_edits"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("games.id"), nullable=False
    )
    edited_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    edit_type: Mapped[GameEditType] = mapped_column(
        SAEnum(GameEditType, native_enum=False, length=30),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False
    )
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_game_edits_game_created", "game_id", "created_at"),
    )
