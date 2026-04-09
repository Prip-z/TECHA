from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ShootingRound(Base):
    __tablename__ = "shooting_rounds"
    __table_args__ = (
        UniqueConstraint("game_id", "round_number", name="uq_shooting_rounds_game_id_round_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shooter_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    target_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
    is_miss: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
