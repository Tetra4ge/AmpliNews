"""Add url and content_hash to articles

Revision ID: b68d3aed869d
Revises: 998e90157435
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b68d3aed869d'
down_revision: Union[str, None] = '998e90157435'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 3 (Tier 1 News Ingestion): both columns back the deduplication
    # strategy - `url` catches exact re-fetches, `content_hash` catches the
    # same story reported under a different URL by another outlet.
    op.add_column('articles', sa.Column('url', sa.String(length=2048), nullable=False, server_default=''))
    op.add_column('articles', sa.Column('content_hash', sa.String(length=64), nullable=False, server_default=''))

    # Drop the temporary server defaults now that existing rows are backfilled -
    # new inserts must always supply both explicitly.
    op.alter_column('articles', 'url', server_default=None)
    op.alter_column('articles', 'content_hash', server_default=None)

    op.create_unique_constraint('uq_articles_url', 'articles', ['url'])
    op.create_unique_constraint('uq_articles_content_hash', 'articles', ['content_hash'])


def downgrade() -> None:
    op.drop_constraint('uq_articles_content_hash', 'articles', type_='unique')
    op.drop_constraint('uq_articles_url', 'articles', type_='unique')
    op.drop_column('articles', 'content_hash')
    op.drop_column('articles', 'url')
