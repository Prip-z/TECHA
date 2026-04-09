from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class VotingRound(Base):
    __tablename__ = "voting_rounds"
    __table_args__ = (
        UniqueConstraint("game_id", "round_number", name="uq_voting_rounds_game_id_round_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_tie: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class VotingNomination(Base):
    __tablename__ = "voting_nominations"
    __table_args__ = (
        UniqueConstraint("voting_round_id", "player_id", name="uq_voting_nominations_round_player"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voting_round_id: Mapped[int] = mapped_column(ForeignKey("voting_rounds.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)


class VotingVote(Base):
    __tablename__ = "voting_votes"
    __table_args__ = (
        UniqueConstraint("voting_round_id", "voter_player_id", name="uq_voting_votes_round_voter"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voting_round_id: Mapped[int] = mapped_column(ForeignKey("voting_rounds.id"), nullable=False, index=True)
    voter_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    target_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
