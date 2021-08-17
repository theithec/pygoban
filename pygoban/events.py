from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from . import board as board_
from . import move as move_
from . import rulesets
from .status import Status


class Event:
    exception: Optional[rulesets.RuleViolation] = None


class Reset(Enum):
    UNDO = "UNDO"
    ANY = "ANY"


@dataclass
class CursorChanged(Event):
    cursor: move_.Move
    board: board_.Board
    next_player: Optional[Status] = None
    reset: Optional[Reset] = None

    def __str__(self):
        return (
            f"{self.__class__.__name__}: {self.cursor} next_player={self.next_player} "
            f"{self.reset}"
        )


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
