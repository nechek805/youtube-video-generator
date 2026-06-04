"""add video_parts table and parts_count column

Revision ID: 0005_add_video_parts
Revises: 0004_add_youtube_accounts
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_add_video_parts"
down_revision = "0004_add_youtube_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parts_count to existing projects (default 1 for all existing rows)
    op.add_column(
        "video_projects",
        sa.Column("parts_count", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "video_parts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("part_number", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("video_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_video_parts_id"), "video_parts", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_video_parts_project_id"), "video_parts", ["project_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_video_parts_project_id"), table_name="video_parts")
    op.drop_index(op.f("ix_video_parts_id"), table_name="video_parts")
    op.drop_table("video_parts")
    op.drop_column("video_projects", "parts_count")
