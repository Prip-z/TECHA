"""add super admin role

Revision ID: e7f8a9b0c1d2
Revises: c1d2e3f4a5b6
Create Date: 2026-04-10 13:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    context = op.get_context()
    with context.autocommit_block():
        op.execute("ALTER TYPE staff_role ADD VALUE IF NOT EXISTS 'super_admin'")
    op.execute(
        sa.text(
            """
            UPDATE admins
            SET role = 'super_admin'
            WHERE id = (
                SELECT id
                FROM admins
                ORDER BY id
                LIMIT 1
            )
            AND NOT EXISTS (
                SELECT 1
                FROM admins
                WHERE role = 'super_admin'
            )
            """
        )
    )


def downgrade() -> None:
    raise NotImplementedError("Downgrade is not supported for enum value removal")
