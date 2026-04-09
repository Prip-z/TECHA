"""scaffold baseline

Revision ID: 0001_scaffold_baseline
Revises:
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_scaffold_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the scaffold baseline."""
    op.create_table(
        "system_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_checks")),
        sa.UniqueConstraint("name", name=op.f("uq_system_checks_name")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO system_checks (id, name, status, created_at)
            VALUES (1, 'migration_check', 'ok', CURRENT_TIMESTAMP)
            """
        )
    )


def downgrade() -> None:
    """Drop the scaffold baseline."""
    op.drop_table("system_checks")
