from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class EventPlayer(Base):
    __tablename__ = "event_player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    games_played: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    paid_amount : Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
