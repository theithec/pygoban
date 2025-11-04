import argparse
import logging
from dataclasses import dataclass, field


from .pos import Pos
from .board import Color, Intersection, Marker, Board
from .game import Game
from .gamecontroller import MainGameController, SubGameController
from .info import GameInfo
from .node import Node
from .nodescontroller import NodesController
from .party import Member, Parties, Party
from .receivers import BaseReceiver
from .rulesets import Ruleset
from .timesettings import TimeSettings

logging.basicConfig(level=logging.DEBUG)


@dataclass
class Settings:
    black_name: str = "Black"
    white_name: str = "White"
    boardsize: int = 19
    komi: float = 7.5
    handicap: int = 0
    min_wait: int = 0
    auto_save: bool = False
    gtp_engines: dict = field(default_factory=dict)
    sgf_path: str | None = None
    mode: str | None = None
    main_time: int = 30
    byoyomi_time: int = 30
    byoyomi_num: int = 3
    byoyomi_stones: int = 1


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("pygoban")
    parser.add_argument("sgf_path", nargs="?", default=None)
    parser.add_argument("-b", "--black-name", help="Black Name")
    parser.add_argument("-w", "--white-name", help="White Name")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("-s", "--boardsize", help="Boardsize", type=int, default=19)
    parser.add_argument("--komi", help="komi", type=float)
    parser.add_argument(
        "--mode", help="Modus(play, edit)", choices=("PLAY", "EDIT"), default="PLAY"
    )
    parser.add_argument(
        "--time", help="[maintime]:[byoyomi_time]:[byoyomi_num]:[byoyomi_stones]"
    )
    return parser


__all__ = [
    "get_argparser",
    "BaseReceiver",
    "Board",
    "Color",
    "Game",
    "GameInfo",
    "Intersection",
    "MainGameController",
    "Marker",
    "Member",
    "Node",
    "NodesController",
    "Parties",
    "Party",
    "Pos",
    "Ruleset",
    "SubGameController",
    "TimeSettings",
]
