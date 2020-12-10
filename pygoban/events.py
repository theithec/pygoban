from typing import Optional, Dict, Set
from dataclasses import dataclass, field
from . import board as board_, GameResult, move as move_, rulesets
from .status import Status


@dataclass
class Event:
    pass


@dataclass
class MovePlayed(Event):
    next_player: Optional[Status] = None
    move: Optional[move_.Move] = None
    extra: Optional[board_.StonelessReason] = None
    is_new: bool = False
    exception: Optional[rulesets.RuleViolation] = None

    def __str__(self):
        return f"Move Played: {self.move} Next: {self.next_player}"


@dataclass
class CursorChanged(Event):
    board: board_.Board
    next_player: Optional[Status] = None
    cursor: Optional[move_.Move] = None
    is_new: bool = True
    exception: Optional[rulesets.RuleViolation] = None

    def __str__(self):
        return f"Cursor changed: {self.cursor}"


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
