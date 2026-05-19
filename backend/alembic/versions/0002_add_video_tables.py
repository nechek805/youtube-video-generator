"""add video tables

Revision ID: 0002_add_video_tables
Revises: 0001_initial
Create Date: 2026-05-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_add_video_tables'
down_revision: Union[str, Sequence[str], None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Per-phase status enums
_prompt_values = ('PENDING', 'READY', 'FAILED')
_video_values = ('PENDING', 'GENERATING', 'READY', 'FAILED')
_metadata_values = ('PENDING', 'READY', 'FAILED')
_workflow_values = ('PROMPT', 'VIDEO', 'METADATA', 'COMPLETED', 'FAILED')


def upgrade() -> None:
    bind = op.get_bind()

    sa.Enum(*_prompt_values, name='promptstatus').create(bind)
    sa.Enum(*_video_values, name='videostatus').create(bind)
    sa.Enum(*_metadata_values, name='metadatastatus').create(bind)
    sa.Enum(*_workflow_values, name='workflowstatus').create(bind)

    op.create_table(
        'video_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        # Prompt phase
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('generated_prompt', sa.Text(), nullable=True),
        sa.Column('edited_prompt', sa.Text(), nullable=True),
        sa.Column(
            'prompt_status',
            postgresql.ENUM(*_prompt_values, name='promptstatus', create_type=False),
            nullable=False,
            server_default='PENDING',
        ),

        # Video phase
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column(
            'video_status',
            postgresql.ENUM(*_video_values, name='videostatus', create_type=False),
            nullable=False,
            server_default='PENDING',
        ),

        # Metadata phase
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'metadata_status',
            postgresql.ENUM(*_metadata_values, name='metadatastatus', create_type=False),
            nullable=False,
            server_default='PENDING',
        ),

        # Overall workflow
        sa.Column(
            'workflow_status',
            postgresql.ENUM(*_workflow_values, name='workflowstatus', create_type=False),
            nullable=False,
            server_default='PROMPT',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # Remove server defaults — handled by the ORM
    for col in ('prompt_status', 'video_status', 'metadata_status', 'workflow_status'):
        op.alter_column('video_projects', col, server_default=None)

    op.create_index(op.f('ix_video_projects_id'), 'video_projects', ['id'], unique=False)
    op.create_index(op.f('ix_video_projects_user_id'), 'video_projects', ['user_id'], unique=False)

    op.create_table(
        'video_generation_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('prompt_used', sa.Text(), nullable=False),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['video_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.alter_column('video_generation_steps', 'is_approved', server_default=None)
    op.create_index(
        op.f('ix_video_generation_steps_id'), 'video_generation_steps', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_video_generation_steps_project_id'),
        'video_generation_steps', ['project_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_video_generation_steps_project_id'), table_name='video_generation_steps'
    )
    op.drop_index(op.f('ix_video_generation_steps_id'), table_name='video_generation_steps')
    op.drop_table('video_generation_steps')

    op.drop_index(op.f('ix_video_projects_user_id'), table_name='video_projects')
    op.drop_index(op.f('ix_video_projects_id'), table_name='video_projects')
    op.drop_table('video_projects')

    bind = op.get_bind()
    sa.Enum(*_workflow_values, name='workflowstatus').drop(bind)
    sa.Enum(*_metadata_values, name='metadatastatus').drop(bind)
    sa.Enum(*_video_values, name='videostatus').drop(bind)
    sa.Enum(*_prompt_values, name='promptstatus').drop(bind)
