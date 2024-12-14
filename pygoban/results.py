from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, Set

from .board import Board, Color, Pos

if TYPE_CHECKING:
    from .stone import Stone


class Event:
    pass


@dataclass
class TurnDone(Event):
    """A players turn, placement or pass"""

    board: Board
    stone: "Stone"
    next_color: Color
    next_time: int | None = None
    killed: Set[Pos] = field(default_factory=set)
    libs: Set[Pos] = field(default_factory=set)
    total_dead: Dict[Color, int] = field(default_factory=lambda: {Color.BLACK: 0, Color.WHITE: 0})
    ko: Pos | None = None


@dataclass
class AnnotationDone(Event):
    pass


@dataclass
class TimeDone(Event):
    """A period ended"""

    color: Color
    next_time: int


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
