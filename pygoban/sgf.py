from typing import Dict, List, Optional
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
        self.variations: List[Move] = []
        self.infos = {**defaults}
        self.game: Optional[Game] = None

    def parse_part(self, part):
        cnt = 0
        while part := part.strip():
            cnt += 1
            if cnt == 1000:
                print(len(part))
                cnt = 0

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
                part = part[match.span(2)[1] :]
            else:
                char = part[0]
                if char == ";":
                    part = part[1:]
                elif char == "(":
                    self.variations.append(self.game.cursor)
                    part = part[1:]
                elif char == ")":
                    self.game._set_cursor(self.variations.pop())
                    part = part[1:]
                else:
                    raise Exception(f"Can not parse: ---\n{part}\n---")

    def parse(self):
        sgftxt = self.sgftxt.strip()[1:-1]
        curr = sgftxt
        cnt = 0
        while curr:
            try:
                cnt += 1
                if cnt == 1000:
                    print(len(curr))
                    cnt = 0
                pos = curr[3:].index(";B[")
                part = curr[: pos + 2]
                self.parse_part(part)
                curr = curr[pos + 2 :]
            except ValueError:
                self.parse_part(curr)
                break
            except Exception:
                print(part)
                raise

    def notsupported(self, name):
        def named(*args, **kwargs):
            print("NOT SUPPORTED YET", name)
            raise Exception("NOT SUPPORTED")

        return named

    def _play_move(self, color, pos, **extras):
        if pos or extras:
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"])) if pos else None
            self.game._test_move(Move(color, coord, **extras), apply_result=True)
        else:
            self.game.pass_(color)

    def _do_deco(self, val, marker):
        parts = val.split("][")
        for pos in parts:
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"]))
            self.game.cursor.extras.decorations[coord] = marker

    def do_tr(self, val):
        self._do_deco(val, "▲")

    def do_ma(self, val):
        self._do_deco(val, "X")

    def do_cr(self, val):
        self._do_deco(val, "●")

    def do_sq(self, val):
        self._do_deco(val, "■")

    def do_b(self, pos):
        self._play_move(BLACK, pos)

    def do_w(self, pos):
        self._play_move(WHITE, pos)

    def do_c(self, cmd):
        self.game.cursor.extras.comments.append(cmd)

    def do_gc(self, cmd):
        self.do_c(cmd)

    def do_lb(self, cmd):
        parts = cmd.split("][")
        for part in parts:
            pos, char = part.split(":")
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"]))
            self.game.cursor.extras.decorations[coord] = char

    def _do_a(self, cmd, color):
        parts = cmd.split("][")
        coords = [sgf_coord_to_gtp(pos, int(self.infos["SZ"])) for pos in parts]
        self._play_move(None, None, stones={color: coords})

    def do_ab(self, cmd):
        self._do_a(cmd, BLACK)

    def do_aw(self, cmd):
        self._do_a(cmd, WHITE)

    def do_ae(self, cmd):
        parts = cmd.split("][")
        for pos in parts:
            coord = sgf_coord_to_gtp(pos, int(self.infos["SZ"]))
            self.game.cursor.extras.empty.add(coord)

    def do_st(self, cmd):
        pass

    def do_vw(self, cmd):
        pass

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
    return parser.game
