from .status import BLACK, WHITE
from .movetree import MoveTree
from .board import letter_coord_from_int


class Game:
    def __init__(self, boardsize, ruleset_cls=None):
        self.movetree = MoveTree(SZ=boardsize)
        self.currentcolor = BLACK
        self.ruleset = ruleset_cls(self)

    def get_othercolor(self, color=None):
        color = color or self.currentcolor
        return BLACK if color == WHITE else WHITE

    def play(self, color, x, y):
        result = self.movetree.test_move(color, x, y)
        self.ruleset.validate(result)
        self.movetree.apply_result(result)
        self.currentcolor = self.get_othercolor(color)
        return result

    def _pass(self, color):
        self.movetree._pass(color)
        self.currentcolor = self.get_othercolor(color)

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.set_cursor(parent)

    def sgf_coords(self, x, y):
        return "%s%s" % (
            letter_coord_from_int(y, self.movetree.board.boardsize),
            x + 1)

    def array_indexes(self, coords):
        xcoord = int(coords[1:]) - 1
        yord = ord(coords[0].upper())
        ycoord = yord - (66 if yord > 72 else 65)
        assert 0 < xcoord < self.movetree.board.boardsize
        assert 0 < ycoord < self.movetree.board.boardsize
        res = xcoord, ycoord
        return res
