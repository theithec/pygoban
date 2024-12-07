from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, Set

from .board import Board, Color, Pos

if TYPE_CHECKING:
    from .stone import Stone


@dataclass
class ColorResult:
    killed: int
    coords: Set[Pos] = field(default_factory=set)

    def total(self):
        return len(self.coords) + self.killed


@dataclass
class GameResult:
    reason: str
    # -type: GameResultType
    winner: Color | None = None
    black: ColorResult | None = None
    white: ColorResult | None = None

    def __getitem__(self, key):
        if key == Color.BLACK:
            return self.black
        if key == Color.WHITE:
            return self.white
        raise KeyError(key)

    def __str__(self) -> str:
        vars_ = vars(self)
        return ", ".join(
            [f"{key}: {val}" for (key, val) in vars_.items() if val and key != "board"]
        )


class ActionType(Enum):
    STONE = "STONE"
    RESET = "RESET"
    RESIGN = "RESIGN"
    ANNOTATED = "ANNOTATED"
    COUNT = "COUNT"
    COUNT_DONE = "COUNT_DONE"


@dataclass
class _StoneResult:
    stone: "Stone"
    next_color: Color

    def __str__(self) -> str:
        vars_ = vars(self)
        return ", ".join(
            [f"{key}: {val}" for (key, val) in vars_.items() if val and key != "board"]
        )


@dataclass
class _StoneResultDefaults:
    killed: Set[Pos] = field(default_factory=set)
    libs: Set[Pos] = field(default_factory=set)
    ko: Pos | None = None
    dead: Dict[Color, int] = field(default_factory=lambda: {Color.BLACK: 0, Color.WHITE: 0})


# @dataclass
# class _ActionResult:


@dataclass
class StoneResult(_StoneResultDefaults, _StoneResult):  # , _ActionResult):
    pass


@dataclass
class ActionResult:  # , _ActionResult):
    type: ActionType
    board: Board
    game_result: GameResult | None = None
    stone_result: StoneResult | None = None

    def __repr__(self) -> str:
        vars_ = vars(self)
        return ", ".join(
            [f"{key}: {val}" for (key, val) in vars_.items() if val and key != "board"]
        )
