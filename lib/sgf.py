import re
from .status import BLACK, WHITE
from . import movetree


SGF_CMD_PATTERN = r"([A-Z]{1,2})((?:\[.*?(?<!\\)\])+).*"

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

INT_KEYS = ("SZ",)


class TreeWriter:
    def __init__(self, tree: movetree.MoveTree):
        self.tree = tree

    def notsupported(self, name, *args, **kwargs):
        def named(*args, **kwargs):
            print("Not supported", name, args, kwargs)
        return named

    def _play_move(self, color, pos):
        if not pos:
            x = y = -1
        else:
            print("P", pos)
            ychar, xchar = pos
            x = 96 - ord(xchar) + int(self.tree.infos["SZ"])
            y = ord(ychar) - 97

        self.tree.test_move(color, x, y, apply_result=True)

    def do_b(self, pos):
        self._play_move(BLACK, pos)

    def do_w(self, pos):
        self._play_move(WHITE, pos)

    def __getitem__(self, name):
        if name.startswith("do_"):
            try:
                return self.__getattribute__(name)
            except AttributeError:
                return self.notsupported(name)

    def __getattr__(self, name):
        return getattr(self.tree, name)


def _parse_moves(moves, pattern, treewriter):
    moves = moves.split(";")
    variations = []

    def parse_move(move):
        org = move
        while move := move.strip():
            match = pattern.match(move)
            if match:
                key, val = match.groups()
                print("KV", key, val)
                move = move[match.span(2)[1]:]
                treewriter[f"do_{key.lower()}"](val[1:-1])
            else:
                for char in move:
                    if not char.strip():
                        continue
                    if char == "(":
                        variations.append(treewriter.cursor)
                    elif char == ")":
                        treewriter.set_cursor(variations.pop())
                    else:
                        raise Exception(f"Can not parse: '{move}' from '{org}'")
                break
    for move in moves:
        parse_move(move)
        print(treewriter.board)


def _parse_intro(intro, pattern):
    infos = {}
    while intro := intro.strip():
        try:
            match = pattern.search(intro)
            key, val = match.groups()
        except AttributeError:
            print("INTRO", intro)
            exit()
            break
        val = val[1:-1]
        if key in INT_KEYS:
            val = int(val)
        infos[key] = val
        intro = intro[match.span(2)[1]:]
    return infos


def parse(sgftxt):
    pattern = re.compile(SGF_CMD_PATTERN, re.DOTALL)
    _, intro, moves = sgftxt.strip()[1:-1].split(";", 2)

    infos = _parse_intro(intro, pattern)
    tree = movetree.MoveTree(**infos)
    _parse_moves(moves, pattern, TreeWriter(tree))
    return tree
