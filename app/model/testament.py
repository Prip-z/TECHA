from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Testament(Base):
    __tablename__ = "testaments"
    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="uq_testaments_game_id_player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)


class TestamentTarget(Base):
    __tablename__ = "testament_targets"
    __table_args__ = (
        UniqueConstraint("testament_id", "position", name="uq_testament_targets_testament_id_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    testament_id: Mapped[int] = mapped_column(ForeignKey("testaments.id"), nullable=False, index=True)
    target_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
