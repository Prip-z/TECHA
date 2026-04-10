"""add app settings

Revision ID: f1a2b3c4d5e6
Revises: f0b2c3d4e5f6_add_staff_roles
Create Date: 2026-04-10 18:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "f0b2c3d4e5f6_add_staff_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=4000), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
        sa.UniqueConstraint("key", name=op.f("uq_app_settings_key")),
    )
    op.execute(
        sa.text("INSERT INTO app_settings (key, value) VALUES (:key, :value)").bindparams(
            key="default_price_per_game",
            value="2500",
        )
    )


def downgrade() -> None:
    op.drop_table("app_settings")
