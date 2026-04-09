from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class GamePlayer(Base):
    __tablename__ = "game_player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("games.game_id"))
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
