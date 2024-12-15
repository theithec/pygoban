import logging
import os
import re
from typing import Dict, List

from pygoban.result import ActionType

from ..board import Color, Marker
from ..pygoban.coords import sgf_to_pos
from ..rulesets import Ruleset
from ..stone import Stone
from . import INFO_PROPS, KEY_TYPES, ROOT_PROPS, ParsingFailed

WHITESPACE_PATTERN = re.compile(" |\t|\n")


class Parser:
    def __init__(self, sgftxt: str, defaults: Dict):
        self.sgftxt = sgftxt
        self.defaults = defaults
        self.defaults.setdefault("HA", 0)
        self.defaults.setdefault("KM", 0.5)
        self.defaults.setdefault("SZ", 19)
        self.variations: List[Stone] = []
        self.infos = {**defaults}
        self.ruleset: Ruleset | None = None
        self.must_match_when_set = {
            "GM": "1",
            "FF": "4",
        }
        self.cursor = Stone(color=Color.EMPTY)
        self.last_cursor = self.cursor

    def poslist(self, val: str):  # means plural of pos
        val = WHITESPACE_PATTERN.sub("", val)
        parts = val.split("][")
        poslist = []
        for part in parts:
            if ":" in part:
                pass  # print("quicklist", part)
            else:
                poslist.append(sgf_to_pos(val))
        return poslist

    def parse(self):
        txt = self.sgftxt
        while txt:


    def _play_move(self, color: Color, coord: str | None, **extras):
        if coord:
            coord = coord.upper()
        if coord == "TT" or not coord:
            pos = None
        else:
            pos = sgf_to_pos(coord)
        self.cursor = Stone(color=color, pos=pos, parent=self.cursor)

    def _do_anno(self, val, marker: Marker):
        for pos in self.poslist(val):
            self.cursor.annos.markers[pos] = marker

    def _do_a(self, val, color):
        poslist = self.poslist(val)
        for pos in poslist:
            self.cursor.annos.stones[pos] = color

    def do_ab(self, val):
        self._do_a(val, Color.BLACK)

    def do_ae(self, cmd):
        self._do_a(cmd, Color.EMPTY)

    def do_ar(self, cmd):
        print("ar", cmd)

    def do_aw(self, cmd):
        self._do_a(cmd, Color.WHITE)

    def do_b(self, coord):
        self._play_move(Color.BLACK, coord)

    def do_bl(self, cmd):
        print("BL", cmd)

    def do_c(self, cmd):
        self.cursor.annos.comment += cmd

    def do_cr(self, val):
        print("cr", val)

    def do_bm(self, cmd):
        print("bm", cmd)

    def do_dd(self, cmd):
        print("dd", cmd)

    def do_do(self, cmd):
        print("do", cmd)

    def do_dm(self, cmd):
        print("dm", cmd)

    def do_gb(self, cmd):
        print("GB", cmd)

    def do_gw(self, cmd):
        print("GW", cmd)

    def do_lb(self, cmd):
        print("CMD", cmd)
        cmd = cmd.replace(os.linesep, "")
        parts = cmd.split("][")
        # print("CMD", cmd)
        for part in parts:
            print("P", part)
            coord, char = part.split(":")
            coord = sgf_to_pos(coord)
            print("LB", char)
            # self.stones.cursor.extras.decorations[coord] = char

    def do_ln(self, cmd):
        print("LN", cmd)

    def do_ma(self, val):
        self._do_anno(val, Marker.MA)

    def do_mn(self, val):
        print("mn", val)

    def do_n(self, cmd):
        print("N", cmd)

    def do_ob(self, cmd):
        print("ob", cmd)

    def do_ow(self, cmd):
        print("ow", cmd)

    def do_pl(self, cmd):
        print("pl", cmd)

    def do_sq(self, val):
        self._do_anno(val, Marker.SQ)

    def do_tr(self, val):
        self._do_anno(val, Marker.TR)

    def do_uc(self, cmd):
        print("uc", cmd)

    def do_te(self, cmd):
        print("te", cmd)

    def do_it(self, cmd):
        print("it", cmd)

    def do_sl(self, cmd):
        print("sl", cmd)

    def do_tw(self, cmd):
        print("tw", cmd)

    def do_tb(self, cmd):
        print("tb", cmd)

    def do_w(self, coord):
        self._play_move(Color.WHITE, coord)

    def do_wl(self, cmd):
        print("wl", cmd)

    def __getitem__(self, name):
        if name.startswith("do_"):
            try:
                return self.__getattribute__(name)
            except AttributeError:
                pass
                # return self.notsupported(name)
        return None


def parse(sgftxt: str, defaults: Dict) -> tuple[Ruleset, Stone]:
    # defaults["HA"] = 0
    # defaults["SZ"] = 19
    parser = Parser(sgftxt, defaults)
    parser.parse()
    assert parser.ruleset
    assert parser.cursor
    return parser.ruleset, parser.cursor


def load(path: str) -> tuple[Ruleset, Stone]:
    with open(path) as fobj:
        sgftxt = fobj.read()
    print("LOADED")
    return parse(sgftxt, {})
    print("LOADED")
    return parse(sgftxt, {})
