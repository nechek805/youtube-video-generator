"""add youtube_accounts

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_add_youtube_accounts"
down_revision = "0003_add_tags_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "youtube_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel_id", sa.String(length=64), nullable=True),
        sa.Column("channel_name", sa.String(length=255), nullable=True),
        sa.Column("channel_thumbnail", sa.Text(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_youtube_accounts_id"), "youtube_accounts", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_youtube_accounts_user_id"),
        "youtube_accounts",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_youtube_accounts_user_id"), table_name="youtube_accounts"
    )
    op.drop_index(
        op.f("ix_youtube_accounts_id"), table_name="youtube_accounts"
    )
    op.drop_table("youtube_accounts")
