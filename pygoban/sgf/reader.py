from typing import Dict, List, Optional
import re
from pygoban.status import BLACK, WHITE
from pygoban.move import Move
from pygoban.game import Game
from pygoban.coords import sgf_to_pos

from . import INFO_KEYS, INT_KEYS, TR, MA, CR, SQ

SGF_CMD_PATTERN = r"([A-Z]{1,2})((?:\[.*?(?<!\\)\])+).*"


def nonescaped_square_bracket_index(txt, from_index=0):
    while index := txt.index("]", from_index):
        if index > 0 and txt[index - 1] == "\\":
            from_index = index + 1
            continue
        return index


def split(txt):
    """
    Iterator that split sgf into parts seperated by valid semicolons
    """
    searchindex = None
    while True:
        try:
            sim = txt.index(";", searchindex or 0)
        except ValueError:
            yield txt
            break
        tmp = txt[(searchindex or 0) : sim]
        # if "bbb" in tmp: import pudb; pudb.set_trace()

        while True:
            try:
                tmp.index("[")
            except ValueError:
                if searchindex is None:
                    break
                searchindex = None
            try:
                bclose = nonescaped_square_bracket_index(tmp)
                tmp = tmp[bclose + 1 :]
            except ValueError:
                searchindex = sim + 1
                break

        if searchindex is not None:
            continue

        searchindex = None
        yield txt[:sim]
        txt = txt[sim + 1 :]


class Enough(Exception):
    pass


class Parser:
    def __init__(self, sgftxt: str, defaults: Dict):
        self.sgftxt = sgftxt
        self.defaults = defaults
        self.pattern = re.compile(SGF_CMD_PATTERN, re.DOTALL)
        self.variations: List[Move] = []
        self.infos = {**defaults}
        self.game: Optional[Game] = None
        self.lv = 0

    def parse_part(self, part):
        cnt = 0
        while part := part.strip():
            cnt += 1
            if cnt == 1000:
                print("p", len(part))
                cnt = 0

            # self.lv += 1
            # if self.lv == 5000:
            #   raise Enough()
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
        # cnt = 0
        for part in split(sgftxt):
            try:
                self.parse_part(part)
            except Enough:
                break
        #     cnt += 1
        #     if cnt % 1000 == 0:
        #         print("c", cnt)
        # print("--")
        # print("C", cnt)

    def notsupported(self, name):
        def named(*args, **kwargs):
            print("NOT SUPPORTED YET", name)
            raise Exception("NOT SUPPORTED")

        return named

    def _play_move(self, color, pos, **extras):
        if pos or extras:
            pos = sgf_to_pos(pos) if pos else None
            self.game.test_move(Move(color, pos, **extras), apply_result=True)
        else:
            self.game.pass_(color)

    def _do_deco(self, val, marker):
        parts = val.split("][")
        for pos in parts:
            coord = sgf_to_pos(pos)
            self.game.cursor.extras.decorations[coord] = marker

    def do_tr(self, val):
        self._do_deco(val, TR)

    def do_ma(self, val):
        self._do_deco(val, MA)

    def do_cr(self, val):
        self._do_deco(val, CR)

    def do_sq(self, val):
        self._do_deco(val, SQ)

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
            coord = sgf_to_pos(pos)
            self.game.cursor.extras.decorations[coord] = char

    def _do_a(self, cmd, color):
        parts = cmd.split("][")
        coords = [sgf_to_pos(pos) for pos in parts]
        self._play_move(None, None, stones={color: coords})

    def do_ab(self, cmd):
        self._do_a(cmd, BLACK)

    def do_aw(self, cmd):
        self._do_a(cmd, WHITE)

    def do_ae(self, cmd):
        parts = cmd.split("][")
        for pos in parts:
            coord = sgf_to_pos(pos)
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
