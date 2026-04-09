"""Import models here so Alembic autogenerate can discover them."""

from .admin import Admin
from .event import Event, EventType
from .event_player import EventPlayer
from .game import Game
from .game_participant import GameParticipant
from .game_player import GamePlayer
from .player import Player
from .shooting_round import ShootingRound
from .system_check import SystemCheck
from .table import Table
from .testament import Testament, TestamentTarget
from .voting_round import VotingNomination, VotingRound, VotingVote

__all__ = [
    "Admin",
    "Event",
    "Game",
    "GameParticipant",
    "Player",
    "ShootingRound",
    "SystemCheck",
    "Table",
    "Testament",
    "TestamentTarget",
    "VotingNomination",
    "VotingRound",
    "VotingVote",
    "EventType",
    "EventPlayer",
    "GamePlayer"
]
