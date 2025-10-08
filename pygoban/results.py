from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, Set, Optional

from .board import Board, Color, Pos

if TYPE_CHECKING:
    from .node import Node
    from .timesettings import Byoyomi
    from .gtp import Role


class Event:
    pass


@dataclass
class TimeData:
    # next_time: dict[Color, int | None] = field(
    #     default_factory=lambda: {Color.BLACK: None, Color.WHITE: None}
    # )
    # byoyomi: Optional["Byoyomi"] = None
    foox: int = 3


@dataclass
class TurnDone(Event):
    """A players turn, placement or pass"""

    board: Board
    node: "Node"
    next_color: Color
    # time: TimeData
    killed: Set[Pos] = field(default_factory=set)
    libs: Set[Pos] = field(default_factory=set)
    total_dead: Dict[Color, int] = field(
        default_factory=lambda: {Color.BLACK: 0, Color.WHITE: 0}
    )
    ko: Pos | None = None
    reset: bool = False


@dataclass
class _GTP(Event):
    name: str
    roles: set["Role"] = field(default_factory=set)


class GTPStarted(_GTP):
    pass


class GTPStopped(_GTP):
    pass


@dataclass
class AnnotationDone(Event):
    pass


@dataclass
class TimeDone(Event):
    """A period ended"""

    color: Color
    next_time: int
    byoyomi: "Byoyomi"


@dataclass
class ColorResult(Event):
    """Result after counting"""

    killed: int
    coords: Set[Pos] = field(default_factory=set)

    def total(self):
        return len(self.coords) + self.killed


@dataclass
class Counted(Event):
    black: ColorResult | None = None
    white: ColorResult | None = None

    def __getitem__(self, color: Color):
        if color == Color.BLACK:
            return self.black
        if color == Color.WHITE:
            return self.white
        raise KeyError(color)


class GameResultType(Enum):
    RESIGN = "RESIGN"
    LOST_BY_TIME = "LOST_BY_TIME"
    COUNTED = "COUNTED"


GAME_RESULT_STR_BY_TYPE: dict[GameResultType, str] = {
    GameResultType.RESIGN: "{color} + resign",
    GameResultType.LOST_BY_TIME: "{color} + time",
    GameResultType.COUNTED: "{color} + {points_diff}",
}


@dataclass
class GameResultDone(Event):
    type: GameResultType
    winner: Color | None = None
    msg: str = ""
