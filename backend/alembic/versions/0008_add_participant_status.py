"""add status column to participants

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "participants",
        sa.Column(
            "status",
            sa.String(length=25),
            nullable=False,
            server_default="active",
        ),
    )


def downgrade() -> None:
    op.drop_column("participants", "status")
