"""add tags column to video_projects

Revision ID: 0003_add_tags_column
Revises: 0002_add_video_tables
Create Date: 2026-05-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0003_add_tags_column'
down_revision: Union[str, Sequence[str], None] = '0002_add_video_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'video_projects',
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('video_projects', 'tags')
