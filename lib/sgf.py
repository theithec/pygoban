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
    "CA",  # encoding
    "ST",  # ?
    #  "GC" "ST", "CA",
)

INT_KEYS = ("SZ",)


class Parser:

    def __init__(self, sgftxt):
        self.sgftxt = sgftxt
        self.pattern = re.compile(SGF_CMD_PATTERN, re.DOTALL)
        self.variations = []
        self.infos = {}
        self.tree = None

    def parse_part(self, part):
        while part := part.strip():
            match = self.pattern.match(part)
            if match:
                key, val = match.groups()
                val = val[1:-1]
                print("KV", key, val)
                if key in INFO_KEYS:
                    if key in INT_KEYS:
                        val = int(val)
                    self.infos[key] = val
                else:
                    self.tree = self.tree or movetree.MoveTree(**self.infos)
                    self[f"do_{key.lower()}"](val)
                part = part[match.span(2)[1]:]
            else:
                for char in part:
                    if not char.strip():
                        continue
                    if char == "(":
                        self.variations.append(self.tree.cursor)
                    elif char == ")":
                        self.tree.set_cursor(self.variations.pop())
                    #else:
                    #    raise Exception(f"Can not parse: '{part}' from '{org}'")
                break

    def parse(self):
        sgftxt = self.sgftxt.strip()[1:-1]
        sgfparts = sgftxt.split(";")
        for part in sgfparts:
            self.parse_part(part)

    def notsupported(self, name):
        def named(*args, **kwargs):
            print("Not supported", name, args, kwargs)
            #  raise Exception("NOT SUPPORTED")
        return named

    def _play_move(self, color, pos):
        if not pos:
            x = y = -1
        else:
            ychar, xchar = pos
            x = 96 - ord(xchar) + int(self.tree.infos["SZ"])
            y = ord(ychar) - 97

        self.tree.test_move(color, x, y, apply_result=True)

    def do_b(self, pos):
        print("PB", pos)
        self._play_move(BLACK, pos)

    def do_w(self, pos):
        self._play_move(WHITE, pos)

    def do_c(self, cmd):
        self.tree.cursor.comments.append(cmd)

    def __getitem__(self, name):
        if name.startswith("do_"):
            try:
                return self.__getattribute__(name)
            except AttributeError:
                return self.notsupported(name)

def parse(sgftxt):
    parser = Parser(sgftxt)
    parser.parse()
    print(parser.tree.board)
    return parser.tree
