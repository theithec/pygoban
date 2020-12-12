from typing import Optional, Dict
from dataclasses import dataclass, field
from . import board as board_, move as move_, rulesets
from .status import Status


@dataclass
class Event:
    pass


@dataclass
class MovePlayed(Event):
    move: move_.Move
    is_new: bool = False
    next_player: Optional[Status] = None
    exception: Optional[rulesets.RuleViolation] = None

    def __str__(self):
        return f"Move Played: {self.move} Next: {self.next_player}"


@dataclass
class CursorChanged(Event):
    board: board_.Board
    next_player: Optional[Status] = None
    cursor: Optional[move_.Move] = None
    is_new: bool = False
    exception: Optional[rulesets.RuleViolation] = None


class MovesReseted(Event):
    def __init__(self, root: move_.Move):
        self.root = root

    def __str__(self):
        return f"Move reseted: {self.root}"


@dataclass
class Counted(Event):
    board: board_.Board
    points: Dict[Status, int] = field(default_factory=dict)
    prisoners: Dict[Status, int] = field(default_factory=dict)


@dataclass
class Ended(Event):
    points: Dict[Status, int] = field(default_factory=dict)
    prisoners: Dict[Status, int] = field(default_factory=dict)
    color: Optional[Status] = None
    msg: str = ""
