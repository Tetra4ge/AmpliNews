"""add s3_archive_url to articles

Revision ID: c57a90f1234a
Revises: 42f4e3a1bffc
Create Date: 2026-08-16 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c57a90f1234a'
down_revision: Union[str, None] = '42f4e3a1bffc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('articles', sa.Column('s3_archive_url', sa.String(length=1024), nullable=True))
    op.alter_column('articles', 'content', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.drop_column('articles', 's3_archive_url')
    op.alter_column('articles', 'content', existing_type=sa.Text(), nullable=False)
