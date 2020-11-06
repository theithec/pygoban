from dataclasses import dataclass, field
import sys
import traceback
from typing import Dict, List

from .status import Status, BLACK, WHITE
from .coords import gtp_coord_to_sgf


class MoveList(list):
    """sgf-like output"""

    def __str__(self):
        items = [str(item) for item in self]
        return "(ml:%s)" % " ".join(items)


@dataclass
class MoveExtras:
    comments: List[str] = field(default_factory=list)
    decorations: Dict[str, str] = field(default_factory=dict)
    stones: Dict = field(default_factory=lambda: {BLACK: set(), WHITE: set()})
    nr = 1
    char = "A"

    def has_stones(self):
        return self.stones[BLACK] or self.stones[WHITE]


class Move:
    def __init__(self, color: Status = None, coord: str = None, parent=None, **extras):
        self.coord = coord
        self.color = color
        self.children: Dict[str, MoveList] = {}
        stones = extras.pop("stones", {})
        self.extras = MoveExtras(**extras)
        self.extras.stones.update(stones)
        self._parent = None
        if parent:
            self.parent = parent

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, _parent):
        self._parent = _parent
        self._parent.children.setdefault(self.coord, MoveList())
        self._parent.children[self.coord].append(self)

    @property
    def is_empty(self):
        return not self.coord

    @property
    def is_pass(self):
        return not self.coord and not self.extras.has_stones()

    @property
    def is_root(self):
        return not self.color and not self.extras.has_stones()

    def real_children(self):
        return {k: v for (k, v) in self.children.values() if not v.is_empty}

    def to_sgf(self, boardsize):
        if self.is_root:
            return ""
        if self.is_pass:
            txt = ""
        elif self.extras.has_stones():
            for status in (BLACK, WHITE):
                sgfcoords = "][".join(
                    [gtp_coord_to_sgf(coord) for coord in self.extras.stones[status]]
                )
                txt = f";A{status.shortval}[{sgfcoords}]"
        else:
            val = gtp_coord_to_sgf(self.coord)
            txt = ";{color_char}[{val}]"
            txt = txt.format(color_char=self.color.shortval, val=val)
        for comment in self.extras.comments:
            if comment:
                txt += f"C[{comment}]"
        return txt

    def __del__(self):
        if self.parent:
            if len(self.parent.children) == 1:
                self.parent.children.pop(self.coord, None)

    def __str__(self):
        return self.to_sgf(19)
