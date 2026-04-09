import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ParticipantRole(str, enum.Enum):
    civilian = "civilian"
    sheriff = "sheriff"
    mafia = "mafia"
    don = "don"


class GameParticipant(Base):
    __tablename__ = "game_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fouls: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    extra_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole, name="participant_role"),
        nullable=False,
    )
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
