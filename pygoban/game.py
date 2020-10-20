from typing import Tuple, Dict

from enum import Enum

from .movetree import MoveTree, Move
from .status import BLACK, WHITE, Status, STATUS
from .coords import gtp_coords


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


class ThreeTimesPassed(Exception):
    def __init__(self, color):
        self.color = color


class Game:

    def __init__(self, boardsize, ruleset_cls=None, handicap=0):
        movetree_kwargs = dict(SZ=int(boardsize))
        if handicap:
            movetree_kwargs["HA"] = int(handicap)
        self._movetree = MoveTree(**movetree_kwargs)
        self.ruleset = ruleset_cls(self)
        self.pass_cnt = 0

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
        self.pass_cnt = 0
        return result

    def pass_(self, color):
        self._movetree.pass_(color)
        self.pass_cnt += 1
        if self.pass_cnt == 3:
            raise ThreeTimesPassed(color)

    def undo(self):
        parent = self._movetree.cursor.parent
        self._movetree.set_cursor(parent)
        self.pass_cnt = 0
