from .board import Board
from .move import Move, MoveList
from .status import BLACK, WHITE


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
        self.root = Move(None)
        self.set_cursor(self.root)

    def test_move(self, color, x, y, apply_result=False):
        result = self.board.result(color, x, y)
        if apply_result:
            self.apply_result(result)

        return result

    def apply_result(self, result):
        self.board.apply_result(result)
        color = result.color
        self.prisoners[color] += len(result.killed)
        self.cursor = Move(color, result.x, result.y, parent=self.cursor)

    def pass_(self, color):
        self.cursor = Move(color, -1, -1, self.cursor)

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
        path = self.get_path()
        self.board = Board(self.board.boardsize)
        self.cursor = self.root
        for move in path:
            self.test_move(move.color, move.x, move.y, apply_result=True)

    def to_sgf(self):
        txt = "(" + "".join([f"{k}[{v}]" for k, v in self.infos.items()])

        def variations(move):
            nonlocal txt
            txt += str(move)
            lenchildren = len(move.children)
            if lenchildren > 1:
                txt += "("
            elif not lenchildren:
                txt += ")"

            for child in move.children:
                variations(child)

        variations(self.root)
        txt += ")"
        return txt
