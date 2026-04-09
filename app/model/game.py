import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class GameStatus(str, enum.Enum):
    preparation = "preparation"
    voting = "voting"
    revote = "revote"
    shooting = "shooting"
    testament = "testament"
    finished = "finished"


class GameResult(str, enum.Enum):
    civilian_win = "civilian_win"
    mafia_win = "mafia_win"
    ppk_civilian_win = "ppk_civilian_win"
    ppk_mafia_win = "ppk_mafia_win"
    draw = "draw"


class Game(Base):
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
    host_staff_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False, index=True)
    game_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, name="game_status"),
        nullable=False,
        default=GameStatus.preparation,
        server_default=GameStatus.preparation.value,
    )
    result: Mapped[GameResult | None] = mapped_column(
        Enum(GameResult, name="game_result"),
        nullable=True,
    )
    protests: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
