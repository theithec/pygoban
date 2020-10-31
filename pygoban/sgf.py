from typing import Dict
import re
from .status import BLACK, WHITE
from .move import Move
from .game import Game, INFO_KEYS
from .coords import sgf_coord_to_gtp


SGF_CMD_PATTERN = r"([A-Z]{1,2})((?:\[.*?(?<!\\)\])+).*"

INT_KEYS = ("SZ", "HA")


class Parser:

    def __init__(self, sgftxt: str, defaults: Dict):
        self.sgftxt = sgftxt
        self.defaults = defaults
        self.pattern = re.compile(SGF_CMD_PATTERN, re.DOTALL)
        self.variations = []
        self.infos = {**defaults}
        self.game: Game = None

    def parse_part(self, part):
        while part := part.strip():
            match = self.pattern.match(part)
            if match:
                key, val = match.groups()
                val = val[1:-1]
                if key in INFO_KEYS:
                    if key in INT_KEYS:
                        val = int(val)
                    self.infos[key] = val
                else:
                    self.game = self.game or Game(**self.infos)
                    self[f"do_{key.lower()}"](val)
                part = part[match.span(2)[1]:]
            else:
                for char in part:
                    if not char.strip():
                        continue
                    if char == "(":
                        self.variations.append(self.game.cursor)
                    elif char == ")":
                        self.game._set_cursor(self.variations.pop())
                    # else:
                    #     raise Exception(f"Can not parse: '{part}' from '{org}'")
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

    def _play_move(self, color, pos, **extras):
        if pos or extras:
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"])) if pos else None
            self.game._test_move(Move(color, coord, **extras), apply_result=True)
        else:
            self.game.pass_(color)

    def do_tr(self, val):
        parts = val.split("][")
        for pos in parts:
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"]))
            self.game.cursor.extras.decorations[coord] = "▲"

    def do_b(self, pos):
        self._play_move(BLACK, pos)

    def do_w(self, pos):
        self._play_move(WHITE, pos)

    def do_c(self, cmd):
        self.game.cursor.extras.comments.append(cmd)

    def do_lb(self, cmd):
        parts = cmd.split("][")
        for part in parts:
            pos, char = part.split(":")
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"]))
            self.game.cursor.extras.decorations[coord] = char

    def _do_a(self, cmd, color):

        parts = cmd.split("][")

        coords = [sgf_coord_to_gtp(pos, int(self.infos["SZ"])) for pos in parts]
        # import pudb; pudb.set_trace()
        self._play_move(None, None, stones={color: coords})
        print("SGF:", self.game.cursor, color, coords)

    def do_ab(self, cmd):
        self._do_a(cmd, BLACK)

    def do_aw(self, cmd):
        self._do_a(cmd, WHITE)

    def __getitem__(self, name):
        if name.startswith("do_"):
            try:
                return self.__getattribute__(name)
            except AttributeError:
                return self.notsupported(name)
        return None


def parse(sgftxt: str, defaults: Dict):
    parser = Parser(sgftxt, defaults)
    parser.parse()
    print(parser.game.board)
    return parser.game
