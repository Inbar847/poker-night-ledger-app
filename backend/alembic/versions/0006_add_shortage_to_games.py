"""add shortage fields to games

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("shortage_amount", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "games",
        sa.Column("shortage_strategy", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("games", "shortage_strategy")
    op.drop_column("games", "shortage_amount")
