import enum

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class GameStatus(str, enum.Enum):
    preparation = "preparation"
    active = "active"
    finished = "finished"


class GameResult(str, enum.Enum):
    civilian = "civilian"
    mafia = "mafia"
    ppk_civilian = "ppk_civilian"
    ppk_mafia = "ppk_mafia"
    continues = "continues"


class Game(Base):
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
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
