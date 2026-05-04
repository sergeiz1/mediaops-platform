"""add file_key to assets

Revision ID: 5f7b2c1f9a11
Revises: 78c603adaf70
Create Date: 2026-05-04 16:05:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f7b2c1f9a11"
down_revision: Union[str, Sequence[str], None] = "78c603adaf70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("file_key", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("assets", "file_key")
