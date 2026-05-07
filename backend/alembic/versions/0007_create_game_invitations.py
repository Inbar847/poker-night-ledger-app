"""create game_invitations table

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_invitations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("game_id", sa.Uuid(as_uuid=True), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("invited_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("invited_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("game_id", "invited_user_id", name="uq_game_invitation_game_user"),
    )
    op.create_index("ix_game_invitations_user_status", "game_invitations", ["invited_user_id", "status"])
    op.create_index("ix_game_invitations_game_status", "game_invitations", ["game_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_game_invitations_game_status", table_name="game_invitations")
    op.drop_index("ix_game_invitations_user_status", table_name="game_invitations")
    op.drop_table("game_invitations")
