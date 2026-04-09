from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class EventPlayer(Base):
    __tablename__ = "event_player"
    __table_args__ = (
        UniqueConstraint("event_id", "player_id", name="uq_event_player_event_id_player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
