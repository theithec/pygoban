from typing import Type

from enum import Enum

from .movetree import MoveTree, Move
from .status import BLACK, WHITE, Status
from .rulesets import BaseRuleset


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


class ThreeTimesPassed(Exception):
    def __init__(self, color):
        self.color = color


class Game:

    def __init__(self, boardsize: int, ruleset_cls: Type[BaseRuleset], handicap: int = 0):
        movetree_kwargs = dict(SZ=int(boardsize))
        if handicap:
            movetree_kwargs["HA"] = int(handicap)
        self._movetree = MoveTree(**movetree_kwargs)
        self.ruleset = ruleset_cls(self)

    @property
    def boardsize(self):
        return self._movetree.board.boardsize

    @property
    def cursor(self):
        return self._movetree.cursor

    @property
    def currentcolor(self):
        return self.get_othercolor(self._movetree.cursor.color)

    def get_othercolor(self, color: Status):
        return BLACK if not color or color == WHITE else WHITE

    def play(self, color, coord):
        move = self.cursor.children.get(
            coord, Move(color, coord))
        result = self._movetree.test_move(move)
        self.ruleset.validate(result)
        self._movetree.apply_result(result, move)
        return result

    def pass_(self, color):
        self._movetree.pass_(color)
        if self.cursor.is_pass and self.cursor.parent and self.cursor.parent.is_pass:
            raise ThreeTimesPassed(color)

    def undo(self):
        parent = self._movetree.cursor.parent
        self._movetree.set_cursor(parent)
