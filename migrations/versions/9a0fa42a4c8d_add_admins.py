"""add admins

Revision ID: 9a0fa42a4c8d
Revises: 6470431ea85e
Create Date: 2026-04-09 20:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a0fa42a4c8d"
down_revision: Union[str, Sequence[str], None] = "6470431ea85e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admins")),
        sa.UniqueConstraint("login", name=op.f("uq_admins_login")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO admins (id, login, name, password_hash, is_active)
            VALUES (
                1,
                'admin',
                'Default Admin',
                'pbkdf2_sha256$120000$00a9a7b0769990f04692e59617f93a9a$50a75c24df8d00f7ac6eae71f458d412aaefb5e91703167871467ecce9334693',
                TRUE
            )
            ON CONFLICT (login) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_table("admins")
