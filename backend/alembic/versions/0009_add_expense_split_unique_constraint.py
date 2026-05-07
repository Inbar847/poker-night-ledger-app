"""add unique constraint on expense_splits (expense_id, participant_id)

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-13
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_expense_split_expense_participant",
        "expense_splits",
        ["expense_id", "participant_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_expense_split_expense_participant",
        "expense_splits",
        type_="unique",
    )
