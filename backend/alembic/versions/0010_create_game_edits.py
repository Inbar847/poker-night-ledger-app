"""create game_edits table for retroactive editing audit trail

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_edits",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("game_id", sa.Uuid(as_uuid=True), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("edited_by_user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("edit_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("before_data", sa.JSON, nullable=True),
        sa.Column("after_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_game_edits_game_created", "game_edits", ["game_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_game_edits_game_created", table_name="game_edits")
    op.drop_table("game_edits")
