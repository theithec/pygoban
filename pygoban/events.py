from typing import Optional, Dict
from dataclasses import dataclass, field
from . import board as board_, move as move_, rulesets
from .status import Status


class Event:
    pass


@dataclass
class CursorChanged(Event):
    cursor: move_.Move
    board: board_.Board
    next_player: Optional[Status] = None
    is_new: bool = False
    exception: Optional[rulesets.RuleViolation] = None

    def __str__(self):
        return f"Cursor Changed: {self.cursor} is_new: {self.is_new} next_player={self.next_player}"


@dataclass
class Counted(Event):
    board: board_.Board
    points: Dict[Status, int] = field(default_factory=dict)
    prisoners: Dict[Status, int] = field(default_factory=dict)


@dataclass
class Ended(Event):
    cursor: move_.Move
    points: Dict[Status, int] = field(default_factory=dict)
    prisoners: Dict[Status, int] = field(default_factory=dict)
    color: Optional[Status] = None
    msg: str = ""
