"""add system checks table

Revision ID: 0002_add_system_checks_table
Revises: 0001_scaffold_baseline
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_system_checks_table"
down_revision: Union[str, Sequence[str], None] = "0001_scaffold_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS system_checks (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                status VARCHAR(32) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO system_checks (id, name, status, created_at)
            SELECT 1, 'migration_check', 'ok', CURRENT_TIMESTAMP
            WHERE NOT EXISTS (
                SELECT 1 FROM system_checks WHERE name = 'migration_check'
            )
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS system_checks"))
