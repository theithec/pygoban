from typing import Tuple, Dict

from enum import Enum

from .movetree import MoveTree
from .status import BLACK, WHITE, Status


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


HANDICAPS: Dict[int, Tuple] = {
    1: ((3, 4),)
}

HANDICAPS[2] = HANDICAPS[1] + ((14, 14),)


class ThreeTimesPassed(Exception):
    def __init__(self, color):
        self.color = color


class Game:

    def __init__(self, boardsize, ruleset_cls=None, handicap=0):
        self.movetree = MoveTree(SZ=boardsize)
        self.currentcolor = BLACK
        self.ruleset = ruleset_cls(self)
        self.handicap = handicap
        self.pass_cnt = 0
        if self.handicap:
            positions = HANDICAPS[handicap]
            for pos in positions:
                self.movetree.board[pos[0]][pos[1]] = BLACK

    @property
    def boardsize(self):
        return self.movetree.board.boardsize

    def get_othercolor(self, color: Status=None):
        color = color or self.currentcolor
        return BLACK if color == WHITE else WHITE

    def play(self, color, x, y):
        result = self.movetree.test_move(color, x, y)
        self.ruleset.validate(result)
        self.movetree.apply_result(result)
        self.currentcolor = self.get_othercolor(color)
        self.pass_cnt = 0
        return result

    def pass_(self, color):
        self.movetree.pass_(color)
        self.pass_cnt += 1
        if self.pass_cnt == 3:
            raise ThreeTimesPassed(color)
        self.currentcolor = self.get_othercolor(color)

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.set_cursor(parent)
        self.pass_cnt = 0
