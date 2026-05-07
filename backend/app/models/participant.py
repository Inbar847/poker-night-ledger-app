import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class ParticipantType(str, enum.Enum):
    registered = "registered"
    guest = "guest"


class RoleInGame(str, enum.Enum):
    dealer = "dealer"
    player = "player"


class ParticipantStatus(str, enum.Enum):
    active = "active"
    left_early = "left_early"
    removed_before_start = "removed_before_start"


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    guest_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participant_type: Mapped[ParticipantType] = mapped_column(
        SAEnum(ParticipantType, native_enum=False, length=20),
        nullable=False,
    )
    role_in_game: Mapped[RoleInGame] = mapped_column(
        SAEnum(RoleInGame, native_enum=False, length=10),
        nullable=False,
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        SAEnum(ParticipantStatus, native_enum=False, length=25),
        nullable=False,
        default=ParticipantStatus.active,
        server_default="active",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    hidden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        # Prevents a registered user from appearing twice in the same game.
        # NULL user_id (guests) is exempt — PostgreSQL and SQLite both treat
        # NULL as distinct in UNIQUE constraints, so multiple guests are allowed.
        UniqueConstraint("game_id", "user_id", name="uq_participant_game_user"),
    )
