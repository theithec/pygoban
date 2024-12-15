import logging


class Pos(tuple):
    """A handcrafted named tuple"""

    def __new__(cls, x, y):
        return super().__new__(cls, (x, y))

    def __init__(self, *_args, **_kwargs):
        self.x = self[0]
        self.y = self[1]


from .board import Color, Intersection, Marker
from .game import Game
from .gamecontroller import GameController
from .info import GameInfo
from .party import Member, Parties, Party
from .receivers import BaseReceiver
from .rulesets import Ruleset
from .node import Node
from .nodescontroller import NodesController
from .timesettings import TimeSettings

logging.basicConfig(level=logging.DEBUG)


__all__ = [
    "BaseReceiver",
    "Color",
    "Game",
    "GameController",
    "Controller",
    "GameInfo",
    "GameResult",
    "Intersection",
    "Marker",
    "Member",
    "Node",
    "NodesController",
    "Parties",
    "Party",
    "Pos",
    "Ruleset",
    "TimeSettings",
]
