from dataclasses import dataclass, field
import sys
import traceback
from typing import Dict, List, Set, Tuple

from .status import Status, BLACK, WHITE
from .coords import gtp_coord_to_sgf, gtp_coords


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
    empty: Set[str] = field(default_factory=set)
    nr = 1
    char = "A"

    def has_stones(self):
        return self.stones[BLACK] or self.stones[WHITE]


class Move:
    def __init__(
        self, color: Status = None, pos: Tuple[int, int] = None, parent=None, **extras
    ):
        self.pos = pos
        self.color = color
        self.children: Dict[str, Move] = {}
        stones = extras.pop("stones", {})
        self._parent = None
        self.extras = MoveExtras(**extras)
        self.extras.stones.update(stones)
        if parent:
            self.parent = parent

    def coord(self, boardsize):
        return gtp_coord_to_sgf(*self.pos, boardsize)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, _parent):
        self._parent = _parent
        self._parent.children.setdefault(self.pos, self)

    @property
    def is_empty(self):
        return not self.pos

    @property
    def is_pass(self):
        return not self.pos and not self.extras.has_stones()

    @property
    def is_root(self):
        return not self.color and not self.extras.has_stones()

    def real_children(self):
        return {k: v for (k, v) in self.children.values() if not v.is_empty}

    def to_sgf(self, boardsize):
        if self.is_root or self.is_pass:
            txt = ""
        if self.extras.has_stones():
            for status in (BLACK, WHITE):
                sgfcoords = "][".join(
                    [gtp_coord_to_sgf(coord) for coord in self.extras.stones[status]]
                )
                txt = f";A{status.shortval}[{sgfcoords}]"
        elif self.pos:
            val = gtp_coord_to_sgf(self.pos)
            txt = ";{color_char}[{val}]"
            txt = txt.format(color_char=self.color.shortval, val=val)
        for comment in self.extras.comments:
            if comment:
                txt += f"C[{comment}]"
        return txt

    def get_path(self):
        path = []
        curr = self
        while curr:
            path.append(curr)
            assert curr != curr.parent
            curr = curr.parent
        path.reverse()
        return path[1:]

    def __del__(self):
        if self.parent:
            if len(self.parent.children) == 1:
                self.parent.children.pop(self.pos, None)

    def __str__(self):
        return ", ".join((str(self.pos) or "-", str(self.color), str(self.extras)))

    def __repr__(self):
        return str(self)
