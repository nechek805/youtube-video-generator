"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum('PENDING', 'ACTIVE', 'DEACTIVATED', 'BANNED', name='emailstatus').create(op.get_bind())

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('email_status', postgresql.ENUM('PENDING', 'ACTIVE', 'DEACTIVATED', 'BANNED', name='emailstatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.alter_column('users', 'email_status', server_default=None)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hashed_session_token', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sessions_hashed_session_token'), 'sessions', ['hashed_session_token'], unique=True)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    op.create_table(
        'email_confirmation_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hashed_token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_email_confirmation_tokens_hashed_token'), 'email_confirmation_tokens', ['hashed_token'], unique=True)
    op.create_index(op.f('ix_email_confirmation_tokens_user_id'), 'email_confirmation_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_confirmation_tokens_user_id'), table_name='email_confirmation_tokens')
    op.drop_index(op.f('ix_email_confirmation_tokens_hashed_token'), table_name='email_confirmation_tokens')
    op.drop_table('email_confirmation_tokens')

    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_hashed_session_token'), table_name='sessions')
    op.drop_table('sessions')

    op.drop_column('users', 'email_status')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

    sa.Enum('PENDING', 'ACTIVE', 'DEACTIVATED', 'BANNED', name='emailstatus').drop(op.get_bind())
