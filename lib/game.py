from enum import Enum
from .status import BLACK, WHITE
from .movetree import MoveTree
from .board import letter_coord_from_int


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


class ThreeTimesPassed(Exception):
    def __init__(self, color):
        self.color = color


class Game:

    def __init__(self, boardsize, ruleset_cls=None):
        self.movetree = MoveTree(SZ=boardsize)
        self.currentcolor = BLACK
        self.ruleset = ruleset_cls(self)
        self.pass_cnt = 0

    def get_othercolor(self, color=None):
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
        self.pass_cnt = 0

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.set_cursor(parent)
        self.pass_cnt = 0

    def sgf_coords(self, x, y):
        return "%s%s" % (
            letter_coord_from_int(y, self.movetree.board.boardsize),
            x + 1)

    def array_indexes(self, coords):
        xcoord = int(coords[1:]) - 1
        yord = ord(coords[0].upper())
        ycoord = yord - (66 if yord > 72 else 65)
        assert 0 <= xcoord < self.movetree.board.boardsize, f"{xcoord}, {coords}"
        assert 0 <= ycoord < self.movetree.board.boardsize, f"{ycoord}, {coords}"
        res = xcoord, ycoord
        return res
