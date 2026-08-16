"""add_rejected_biased_to_reading_history

Revision ID: 42f4e3a1bffc
Revises: b68d3aed869d
Create Date: 2026-08-16 09:32:28.544509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42f4e3a1bffc'
down_revision: Union[str, None] = 'b68d3aed869d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reading_history', sa.Column('rejected_biased', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('reading_history', 'rejected_biased')

