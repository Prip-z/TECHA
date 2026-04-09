"""add staff roles

Revision ID: f0b2c3d4e5f6
Revises: d419cb9890c1
Create Date: 2026-04-09 23:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "d419cb9890c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    staff_role = sa.Enum("admin", "host", name="staff_role")
    staff_role.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "admins",
        sa.Column("role", staff_role, nullable=False, server_default="admin"),
    )
    op.execute(sa.text("UPDATE admins SET role = 'admin' WHERE role IS NULL"))
    op.alter_column("admins", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("admins", "role")
    sa.Enum("admin", "host", name="staff_role").drop(op.get_bind(), checkfirst=True)
