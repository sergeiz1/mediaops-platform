"""add processing timestamps and error

Revision ID: cd3e5a81f42b
Revises: 5f7b2c1f9a11
Create Date: 2026-05-05 10:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cd3e5a81f42b"
down_revision: str | None = "5f7b2c1f9a11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assets", sa.Column("processing_finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assets", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "last_error")
    op.drop_column("assets", "processing_finished_at")
    op.drop_column("assets", "processing_started_at")
