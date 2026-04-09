"""Import models here so Alembic autogenerate can discover them."""

from .admin import StaffRole, StaffUser
from .event import Event, EventType
from .event_player import EventPlayer
from .game import Game, GameResult, GameStatus
from .game_participant import GameParticipant, ParticipantRole
from .player import Player
from .shooting_round import ShootingRound
from .system_check import SystemCheck
from .table import Table
from .testament import Testament, TestamentTarget
from .voting_round import VotingNomination, VotingRound, VotingVote

__all__ = [
    "Event",
    "EventPlayer",
    "EventType",
    "Game",
    "GameParticipant",
    "GameResult",
    "GameStatus",
    "ParticipantRole",
    "Player",
    "ShootingRound",
    "StaffRole",
    "StaffUser",
    "SystemCheck",
    "Table",
    "Testament",
    "TestamentTarget",
    "VotingNomination",
    "VotingRound",
    "VotingVote",
]
