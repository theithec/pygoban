import logging
import os
import re
from typing import Callable, Dict, List

from pygoban import Color, GameInfo, Marker, Node, TimeSettings, coords, rulesets

from . import INFO_PROPS, NODE_PROPS, ROOT_PROPS

WHITESPACE_PATTERN = re.compile(" |\t|\n")


class Parser:

    class ParsingError(Exception):
        pass

    def __init__(self, sgftxt: str, defaults: Dict):
        self.sgftxt = sgftxt
        self.defaults = defaults
        self.defaults.setdefault("HA", 0)
        self.defaults.setdefault("KM", 0.5)
        self.defaults.setdefault("SZ", 19)
        self.defaults.setdefault("PL", "Black")
        self.defaults.setdefault("PB", "Black")
        self.defaults.setdefault("PW", "White")
        self.defaults.setdefault("RU", "Japanese")
        self.variations: List[Node] = []
        self.infos = {**defaults}
        self.ruleset: rulesets.BaseRuleset | None = None
        self.must_match_when_set = {
            "GM": "1",
            "FF": "4",
        }
        self.cursor = Node(color=Color.EMPTY, pos=None)
        self.last_char = None
        self.node_started = False
        self.val_started = False
        self.curr_cmd = ""
        self.curr_val = ""
        self.node_props: dict[str, list[str]] = {}
        self.colors = {"B": Color.BLACK, "W": Color.WHITE}

    def parse_timesettings(self) -> TimeSettings:
        try:
            maintime = int(self.infos["TM"])
        except (ValueError, KeyError) as err:
            raise self.ParsingError(err)

        try:
            byoyomi_time = 30
            byoyomi_stones = 1
            byoyomi_num = 3
        except KeyError as err:

            raise self.ParsingError(err)

        return TimeSettings(
            maintime=maintime,
            byoyomi_num=byoyomi_num,
            byoyomi_stones=byoyomi_stones,
            byoyomi_time=byoyomi_time,
            use_clock=False,
        )

    def add_stone(self):
        color = Color.EMPTY
        pos = None

        if not self.ruleset:
            self.infos.update({key: val[0] for key, val in self.node_props.items()})
            info = GameInfo(
                names={Color.BLACK: self.infos["PB"], Color.WHITE: self.infos["PW"]},
                ranks={Color.BLACK: self.infos.get("BR"), Color.WHITE: self.infos.get("WR")},
                result=self.infos["RE"],
                ruleset=self.infos["RU"],
            )
            # print("OT?", self.infos["TM"], self.infos["OT"])
            # maintime = self.infos["TM"]
            try:
                timesettings = self.parse_timesettings()
            except self.ParsingError as err:
                logging.error(err)
                timesettings = None
            self.ruleset = rulesets.by_key[rulesets.Key.JAPANESE](
                boardsize=int(self.infos["SZ"]),
                komi=float(self.infos["KM"]),
                handicap=int(self.infos["HA"]),
                info=info,
                first=self.infos["PL"],
                timesettings=timesettings,
            )
        else:
            for colchr in ("B", "W"):
                if colchr in self.node_props:
                    color = self.colors[colchr]
                    coord = self.node_props[colchr][0]
                    pos = coords.sgf_to_pos(coord) if coord and coord.lower() != "tt" else None
                    self.node_props.pop(colchr)
                    break
            self.cursor = Node(color=color, pos=pos, parent=self.cursor)
        for key, val in self.node_props.items():
            if key in ROOT_PROPS:
                assert (
                    self.cursor.parent is None or len(self.cursor.parent.children) > 1
                ), f"{key}={val} / {self.cursor}"
                self.infos[key] = val[0]
            elif key in INFO_PROPS:
                self.infos[key] = val[0]
            elif key in NODE_PROPS:
                self.cursor.annos.infos[key] = val[0]

            else:
                self[f"do_{key.lower()}"](val)
            # self[f"do_{key.lower()}"](val)

    def start_vari(self):
        self.node_ended()
        self.variations.append(self.cursor)

    def end_vari(self):
        self.node_ended()
        self.node_started = False
        self.node_props = {}
        self.cursor = self.variations.pop()

    def node_ended(self):
        if self.node_props:
            self.add_stone()
        self.node_props = {}
        self.node_started = False
        self.curr_cmd = ""
        self.curr_val = ""

    def start_node(self):
        self.node_ended()
        self.node_started = True

    def start_val(self):
        self.val_started = True

    def end_val(self):
        self.val_started = False

        assert self.curr_cmd
        assert self.curr_val or self.curr_cmd in (
            "AB",
            "B",
            "BR",
            "DO",
            "EV",
            "GN",
            "IT",
            "OT",
            "PC",
            "RE",
            "SO",
            "TM",
            "VW",
            "W",
            "WR",
        ), f"{self.curr_cmd} / {self.curr_val}"
        self.node_props.setdefault(self.curr_cmd, [])
        self.node_props[self.curr_cmd].append(self.curr_val)
        self.curr_val = ""

    def parse(self):
        for _, char in enumerate(self.sgftxt):
            # if _ == 2000:
            #    break
            if char in (" ", "\\n", "\\t", os.linesep):
                if not self.val_started:
                    continue
            last_char = self.last_char
            self.last_char = char
            last_is_escape = last_char == "\\"
            if self.val_started:
                assert self.node_started

            def info():
                print(
                    "last",
                    last_char,
                    "char",
                    char,
                    "val_started",
                    self.val_started,
                    "node started",
                    self.node_started,
                    "cmd",
                    self.curr_cmd,
                    "val",
                    self.curr_val[:5],
                    "...",
                    self.curr_val[-5:-1],
                    "(",
                    len(self.curr_val),
                    ")",
                    "lastesc",
                    last_is_escape,
                )

            # info()
            match char:
                case "(" if not self.val_started:
                    self.start_vari()
                case ")" if not self.val_started:
                    self.end_vari()
                case ";" if not self.val_started:
                    self.start_node()
                case "[" if not self.val_started:
                    self.start_val()
                case "]" if not last_is_escape:
                    self.end_val()
                case _:
                    if last_char == "]" and not self.curr_val.endswith("\\]"):
                        self.curr_cmd = ""
                    #    # self.end_val()
                    #    print("del cmd")
                    #    self.curr_cmd = char

                    if self.val_started:
                        self.curr_val += char
                    else:
                        self.curr_cmd += char

    def notsupported(self, name):
        def named(*args, **kwargs):
            logging.warning("NOT SUPPORTED: %s %s %s", name, args, kwargs)

        return named

    def __getitem__(self, name) -> Callable:
        if name.startswith("do_"):
            try:
                return self.__getattribute__(name)
            except AttributeError:
                pass
        return self.notsupported(name)

    def _do_a(self, val, color: Color):
        for coord in val:
            if coord:
                for pos in coords.sgf_to_poslist(coord):
                    self.cursor.annos.stones[pos] = color

    def _do_l(self, val, color: Color):
        # self.cursor.annos.time_left[color] = val[0]
        print("DO L", val, color)
        self.cursor.annos.time_left = val[0]

    def _do_o(self, val, color: Color):

        print("DO O", val, color)
        # self.cursor.annos.stones_left[color] = val[0]
        self.cursor.annos.stones_left = val[0]

    def _do_own(self, val, color: Color):
        for coordset in val:
            for pos in coords.sgf_to_poslist(coordset):
                self.cursor.annos.owned[pos] = color

    def _do_marker(self, val, marker: Marker):
        for coordset in val:
            for pos in coords.sgf_to_poslist(coordset):
                self.cursor.annos.markers[pos] = marker

    def do_ab(self, val):
        self._do_a(val, Color.BLACK)

    def do_ae(self, val):
        self._do_a(val, Color.EMPTY)

    def do_aw(self, val):
        self._do_a(val, Color.WHITE)

    def do_ar(self, val):
        for pair in val:
            poslist = [coords.sgf_to_pos(sgfpos) for sgfpos in pair.split(":")]
            self.cursor.annos.arrows.append(tuple(poslist))

    def do_bl(self, val):
        self._do_l(val, Color.BLACK)

    def do_c(self, val):
        self.cursor.annos.comment = val[0]

    def do_ma(self, val):
        self._do_marker(val, Marker.MA)

    def do_cr(self, val):
        self._do_marker(val, Marker.CR)

    def do_dd(self, val):
        self._do_marker(val, Marker.DIMMED)

    def do_ha(self, val):
        self.infos["HA"] = val[0]

    def do_lb(self, vals):
        for val in vals:
            coord, txt = val.split(":")
            pos = coords.sgf_to_pos(coord)
            self.cursor.annos.chars[pos] = txt

    def do_ln(self, val):
        for pair in val:
            poslist = [coords.sgf_to_pos(sgfpos) for sgfpos in pair.split(":")]
            self.cursor.annos.lines.append(tuple(poslist))

    def do_ob(self, val):
        self._do_o(val, Color.BLACK)

    def do_ow(self, val):
        self._do_o(val, Color.BLACK)

    def do_sl(self, val):
        self._do_marker(val, Marker.MA)

    def do_sq(self, val):
        self._do_marker(val, Marker.SQ)

    def do_tr(self, val):
        self._do_marker(val, Marker.TR)

    def do_tb(self, val):
        self._do_own(val, Color.BLACK)

    def do_tw(self, val):
        self._do_own(val, Color.WHITE)

    def do_wl(self, val):
        self._do_l(val, Color.WHITE)


def parse(sgftxt: str, defaults: Dict) -> tuple[rulesets.BaseRuleset, Node]:
    parser = Parser(sgftxt, defaults)
    parser.parse()
    assert parser.ruleset and parser.cursor, f"{parser.ruleset} / {parser.cursor}"
    return parser.ruleset, parser.cursor  # .root()


def load(path: str) -> tuple[rulesets.BaseRuleset, Node]:
    with open(path, encoding="utf-8") as fobj:
        sgftxt = fobj.read()
    ruleset, cursor = parse(sgftxt, {})
    return ruleset, cursor
