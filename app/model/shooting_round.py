from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ShootingRound(Base):
    __tablename__ = "shooting_rounds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shooter_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    target_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
