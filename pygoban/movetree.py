from typing import Tuple, Dict
from .board import Board
from .move import Move, MoveList
from .status import BLACK, WHITE
from .coords import array_indexes

HANDICAPS: Dict[int, Tuple] = {
    1: ((3, 3),)
}

HANDICAPS[2] = HANDICAPS[1] + ((15, 15),)


class MoveTree:
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
        # "GC" "ST", "CA",
    )

    def __init__(self, **infos):
        self.board = Board(int(infos["SZ"]))
        self.infos = infos
        self.root = Move(color=None, coord=None)
        self.set_cursor(self.root)

    def set_handicap(self):
        handicap = self.infos.get("HA")
        if not handicap:
            return
        positions = HANDICAPS.get(handicap, tuple())
        for pos in positions:
            self.board[pos[0]][pos[1]] = BLACK

    def test_move(self, move, apply_result=False):
        result = self.board.result(move.color, *array_indexes(move.coord, self.board.boardsize))
        if apply_result:
            self.apply_result(result, move)

        return result

    def apply_result(self, result, move=None):
        self.board.apply_result(result)
        color = result.color
        self.prisoners[color] += len(result.killed)
        old_cursor = self.cursor
        self.cursor = move
        move.parent = old_cursor

    def pass_(self, color):
        self.cursor = Move(color, coord=None, parent=self.cursor)

    def get_path(self):
        path = MoveList()
        curr = self.cursor
        while curr:
            path.append(curr)
            curr = curr.parent
        path.reverse()
        return path[1:]

    def set_cursor(self, move):
        self.cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self.set_handicap()
        path = self.get_path()
        self.cursor = self.root
        for pmove in path:
            self.test_move(pmove, apply_result=True)

    def to_sgf(self):
        txt = "(;" + "".join([f"{k}[{v}]" for k, v in self.infos.items()])
        boardsize = self.board.boardsize

        def variations(move):
            nonlocal txt
            txt += move.to_sgf(boardsize)
            lenchildren = len(move.children)
            if lenchildren > 1:
                txt += "("
            elif not lenchildren:
                txt += ")"

            for child in move.children.values():
                variations(child)

        variations(self.root)
        return txt
