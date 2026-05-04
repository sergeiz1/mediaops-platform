"""create assets table

Revision ID: 78c603adaf70
Revises: 
Create Date: 2026-05-04 14:46:16.121193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '78c603adaf70'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    asset_status = postgresql.ENUM(
        "uploaded",
        "processing",
        "ready",
        "failed",
        name="asset_status",
        create_type=False,
    )
    asset_visibility = postgresql.ENUM(
        "private",
        "public",
        name="asset_visibility",
        create_type=False,
    )

    asset_status.create(op.get_bind(), checkfirst=True)
    asset_visibility.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("speaker", sa.String(length=255), nullable=True),
        sa.Column("event_name", sa.String(length=255), nullable=True),
        sa.Column("status", asset_status, nullable=False, server_default="uploaded"),
        sa.Column("visibility", asset_visibility, nullable=False, server_default="private"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assets_id", "assets", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_assets_id", table_name="assets")
    op.drop_table("assets")

    asset_visibility = postgresql.ENUM("private", "public", name="asset_visibility")
    asset_status = postgresql.ENUM("uploaded", "processing", "ready", "failed", name="asset_status")
    asset_visibility.drop(op.get_bind(), checkfirst=True)
    asset_status.drop(op.get_bind(), checkfirst=True)
