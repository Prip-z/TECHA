"""normalize game scaffold

Revision ID: c1d2e3f4a5b6
Revises: f0b2c3d4e5f6
Create Date: 2026-04-10 00:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "f0b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_game_status = postgresql.ENUM("preparation", "active", "finished", name="game_status_old")
new_game_status = postgresql.ENUM(
    "preparation",
    "voting",
    "revote",
    "shooting",
    "testament",
    "finished",
    name="game_status",
)
old_game_result = postgresql.ENUM(
    "civilian",
    "mafia",
    "ppk_civilian",
    "ppk_mafia",
    "continues",
    name="game_result_old",
)
new_game_result = postgresql.ENUM(
    "civilian_win",
    "mafia_win",
    "ppk_civilian_win",
    "ppk_mafia_win",
    "draw",
    name="game_result",
)


def upgrade() -> None:
    op.execute("ALTER TYPE game_status RENAME TO game_status_old")
    new_game_status.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE games ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE games
        ALTER COLUMN status TYPE game_status
        USING (
            CASE status::text
                WHEN 'active' THEN 'voting'
                ELSE status::text
            END
        )::game_status
        """
    )
    op.execute("ALTER TABLE games ALTER COLUMN status SET DEFAULT 'preparation'")
    old_game_status.drop(op.get_bind(), checkfirst=False)

    op.execute("ALTER TYPE game_result RENAME TO game_result_old")
    new_game_result.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE games ALTER COLUMN result DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE games
        ALTER COLUMN result TYPE game_result
        USING (
            CASE result::text
                WHEN 'civilian' THEN 'civilian_win'
                WHEN 'mafia' THEN 'mafia_win'
                WHEN 'ppk_civilian' THEN 'ppk_civilian_win'
                WHEN 'ppk_mafia' THEN 'ppk_mafia_win'
                WHEN 'continues' THEN 'draw'
                ELSE result::text
            END
        )::game_result
        """
    )
    old_game_result.drop(op.get_bind(), checkfirst=False)

    op.add_column("games", sa.Column("host_staff_id", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("protests", sa.String(length=4000), nullable=True))
    op.add_column("games", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("games", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_games_host_staff_id_admins", "games", "admins", ["host_staff_id"], ["id"])
    op.create_index(op.f("ix_games_host_staff_id"), "games", ["host_staff_id"], unique=False)
    op.execute(
        """
        UPDATE games
        SET host_staff_id = (
            SELECT id
            FROM admins
            ORDER BY id
            LIMIT 1
        )
        WHERE host_staff_id IS NULL
        """
    )
    op.alter_column("games", "host_staff_id", nullable=False)

    op.alter_column(
        "event_player",
        "paid_amount",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        postgresql_using="paid_amount::double precision",
        existing_nullable=False,
    )
    op.create_unique_constraint("uq_event_player_event_id_player_id", "event_player", ["event_id", "player_id"])
    op.create_unique_constraint("uq_tables_name", "tables", ["name"])

    op.alter_column(
        "game_participants",
        "score",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        postgresql_using="score::double precision",
        existing_nullable=False,
    )
    op.alter_column(
        "game_participants",
        "extra_score",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        postgresql_using="extra_score::double precision",
        existing_nullable=False,
    )
    op.alter_column("game_participants", "role", server_default="civilian")
    op.create_unique_constraint(
        "uq_game_participants_game_id_player_id",
        "game_participants",
        ["game_id", "player_id"],
    )
    op.create_unique_constraint(
        "uq_game_participants_game_id_seat_number",
        "game_participants",
        ["game_id", "seat_number"],
    )

    op.alter_column("shooting_rounds", "target_player_id", nullable=True)
    op.add_column(
        "shooting_rounds",
        sa.Column("is_miss", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_unique_constraint(
        "uq_shooting_rounds_game_id_round_number",
        "shooting_rounds",
        ["game_id", "round_number"],
    )

    op.add_column(
        "voting_rounds",
        sa.Column("is_revote", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "voting_rounds",
        sa.Column("is_lift_applied", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "voting_rounds",
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("voting_rounds", sa.Column("eliminated_player_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_voting_rounds_eliminated_player_id_players",
        "voting_rounds",
        "players",
        ["eliminated_player_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_voting_rounds_eliminated_player_id"),
        "voting_rounds",
        ["eliminated_player_id"],
        unique=False,
    )

    op.drop_table("game_player")
    op.drop_column("system_checks", "lol")


def downgrade() -> None:
    op.add_column(
        "system_checks",
        sa.Column("lol", sa.String(length=32), nullable=True, server_default="NIGGERS"),
    )
    op.create_table(
        "game_player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=True),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.game_id"], name=op.f("fk_game_player_game_id_games")),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name=op.f("fk_game_player_player_id_players")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_player")),
    )

    op.drop_index(op.f("ix_voting_rounds_eliminated_player_id"), table_name="voting_rounds")
    op.drop_constraint("fk_voting_rounds_eliminated_player_id_players", "voting_rounds", type_="foreignkey")
    op.drop_column("voting_rounds", "eliminated_player_id")
    op.drop_column("voting_rounds", "is_completed")
    op.drop_column("voting_rounds", "is_lift_applied")
    op.drop_column("voting_rounds", "is_revote")

    op.drop_constraint("uq_shooting_rounds_game_id_round_number", "shooting_rounds", type_="unique")
    op.drop_column("shooting_rounds", "is_miss")
    op.alter_column("shooting_rounds", "target_player_id", nullable=False)

    op.drop_constraint("uq_game_participants_game_id_seat_number", "game_participants", type_="unique")
    op.drop_constraint("uq_game_participants_game_id_player_id", "game_participants", type_="unique")
    op.alter_column("game_participants", "role", server_default=None)
    op.alter_column(
        "game_participants",
        "extra_score",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="ROUND(extra_score)::integer",
        existing_nullable=False,
    )
    op.alter_column(
        "game_participants",
        "score",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="ROUND(score)::integer",
        existing_nullable=False,
    )

    op.drop_constraint("uq_tables_name", "tables", type_="unique")
    op.drop_constraint("uq_event_player_event_id_player_id", "event_player", type_="unique")
    op.alter_column(
        "event_player",
        "paid_amount",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="ROUND(paid_amount)::integer",
        existing_nullable=False,
    )

    op.drop_index(op.f("ix_games_host_staff_id"), table_name="games")
    op.drop_constraint("fk_games_host_staff_id_admins", "games", type_="foreignkey")
    op.drop_column("games", "finished_at")
    op.drop_column("games", "started_at")
    op.drop_column("games", "protests")
    op.drop_column("games", "host_staff_id")

    op.execute("ALTER TYPE game_result RENAME TO game_result_old")
    old_game_result.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE games ALTER COLUMN result DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE games
        ALTER COLUMN result TYPE game_result_old
        USING (
            CASE result::text
                WHEN 'civilian_win' THEN 'civilian'
                WHEN 'mafia_win' THEN 'mafia'
                WHEN 'ppk_civilian_win' THEN 'ppk_civilian'
                WHEN 'ppk_mafia_win' THEN 'ppk_mafia'
                WHEN 'draw' THEN 'continues'
                ELSE result::text
            END
        )::game_result_old
        """
    )
    new_game_result.drop(op.get_bind(), checkfirst=False)
    op.execute("ALTER TYPE game_result_old RENAME TO game_result")

    op.execute("ALTER TYPE game_status RENAME TO game_status_old")
    old_game_status.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE games ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE games
        ALTER COLUMN status TYPE game_status_old
        USING (
            CASE status::text
                WHEN 'voting' THEN 'active'
                WHEN 'revote' THEN 'active'
                WHEN 'shooting' THEN 'active'
                WHEN 'testament' THEN 'active'
                ELSE status::text
            END
        )::game_status_old
        """
    )
    op.execute("ALTER TABLE games ALTER COLUMN status SET DEFAULT 'preparation'")
    new_game_status.drop(op.get_bind(), checkfirst=False)
    op.execute("ALTER TYPE game_status_old RENAME TO game_status")
