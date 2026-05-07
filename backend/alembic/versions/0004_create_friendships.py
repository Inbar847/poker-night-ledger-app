"""create friendships table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friendships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requester_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("addressee_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.String(length=10),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "requester_user_id",
            "addressee_user_id",
            name="uq_friendship_requester_addressee",
        ),
    )
    op.create_index(
        "ix_friendships_addressee_status",
        "friendships",
        ["addressee_user_id", "status"],
    )
    op.create_index(
        "ix_friendships_requester_status",
        "friendships",
        ["requester_user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_friendships_requester_status", table_name="friendships")
    op.drop_index("ix_friendships_addressee_status", table_name="friendships")
    op.drop_table("friendships")
