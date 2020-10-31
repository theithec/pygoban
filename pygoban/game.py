from enum import Enum
from typing import Dict, Tuple

from .board import Board, StonelessResult, StonelessReason
from .coords import array_indexes
from .move import Move
from .rulesets import BaseRuleset
from .status import BLACK, WHITE, Status


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


class ThreeTimesPassed(Exception):
    def __init__(self, color):
        self.color = color


HANDICAPS: Dict[int, Tuple] = {
    1: ((3, 3),)
}
HANDICAPS[2] = HANDICAPS[1] + ((15, 15),)

INFO_KEYS = (
    "GM",  # 1 = go
    "FF",  # File format
    "AP",  # Application
    "RU",  # Ruleset,
    "SZ",  # Size,
    "AN",  # Annotations: name of the person commenting the game.
    "BR", "WR",  # Rank,
    "BT", "WT",  # Team
    "CP",  # Copyright
    "DT",  # Date,
    "EV",  # Event
    "GN",  # Game name,
    "HA",  # Handicap,
    "KM",  # KOmi,
    "ON",  # OPening,
    "OT",  # Overtime
    "PB", "PW",  # Player Name,
    "PC",  # Place
    "PL",  # Start color
    "RE",  # Result,
    "RO",  # Round
    "SO",  # Source
    "TM",  # Time limits
    "US",  # user (file creator)
    "CA",  # Encoding
    # "GC" "ST",
)


class Game:

    def __init__(self, **infos):
        self.infos = {k: v for k in INFO_KEYS if (v := infos.get(k))}
        self.board = Board(int(infos["SZ"]))
        self.ruleset = BaseRuleset(self)
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.root = Move(color=None, coord=None)
        self._cursor = self.root

    @property
    def boardsize(self):
        return self.board.boardsize

    @property
    def currentcolor(self):
        return self.get_othercolor(self.cursor.color)

    @property
    def cursor(self):
        return self._cursor

    def get_othercolor(self, color: Status):
        return BLACK if not color or color == WHITE else WHITE

    def play(self, color, coord):
        children = self.cursor.children.get(coord)
        move = None
        if children:
            for child in children:
                if child.color == color:
                    move = child
                    break
        if not move:
            move = Move(color, coord)
        result = self._test_move(move)
        self.ruleset.validate(result)
        self._apply_result(result, move)
        return result

    def pass_(self, color):

        if self.cursor.is_pass and self.cursor.parent and self.cursor.parent.is_pass:
            raise ThreeTimesPassed(color)
        self._cursor = Move(color, coord=None, parent=self.cursor)

    def undo(self):
        parent = self.cursor.parent
        self._set_cursor(parent)

    def to_sgf(self):
        txt = "(;" + "".join([f"{k}[{v}]" for k, v in self.infos.items()])
        boardsize = self.board.boardsize
        has_variations = False

        def add_children(move):
            nonlocal txt, has_variations

            parent = move.parent
            is_variation = parent and parent.children and len(parent.children) > 1
            if is_variation:
                txt += "("
            txt += move.to_sgf(boardsize)

            for childlist in move.children.values():
                for child in childlist:
                    add_children(child)
            if is_variation:
                txt += ")"

        add_children(self.root)
        txt += ")"
        return txt

    def _set_cursor(self, move):
        self._cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self._set_handicap()
        path = self._get_path()
        self._cursor = self.root
        for pmove in path:
            self._test_move(pmove, apply_result=True)

    def _test_move(self, move, apply_result=False):
        if move.coord:
            result = self.board.result(move.color, *array_indexes(move.coord, self.board.boardsize))
        else:
            extra = StonelessReason.PASS if move.is_pass else StonelessReason.ADD_STONES
            result = StonelessResult(color=None, extra=extra)
        if apply_result:
            self._apply_result(result, move)

        return result

    def _apply_result(self, result, move=None):
        color = result.color
        old_cursor = self.cursor
        if color:
            self.board.apply_result(result)
            self.prisoners[color] += len(result.killed)
            old_cursor = self.cursor
        elif move.extras.has_stones():
            for status in (BLACK, WHITE):
                coords = move.extras.stones[status]
                for coord in coords:
                    x, y = array_indexes(coord, self.boardsize)
                    self.board[x][y] = status
        self._cursor = move
        move.parent = old_cursor

    def _set_handicap(self):
        handicap = self.infos.get("HA")
        if not handicap:
            return
        positions = HANDICAPS.get(handicap, tuple())
        for pos in positions:
            self.board[pos[0]][pos[1]] = BLACK

    def _get_path(self):
        path = []
        curr = self.cursor
        while curr:
            path.append(curr)
            curr = curr.parent
        path.reverse()
        return path[1:]
