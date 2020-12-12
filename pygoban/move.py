from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Union
from enum import Enum
from .status import Status, BLACK, WHITE


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


class Empty(Enum):
    FIRST_MOVE = "first_move"
    UNDO = "undo"
    PASS = "pass"
    ADD_STONES = "ADD_STONES"
    RESIGN = "RESIGN"


class Move:
    def __init__(
        self,
        color: Status = None,
        pos: Union[Tuple[int, int], Empty] = None,
        parent=None,
        **extras
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

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, _parent):
        self._parent = _parent
        self._parent.children.setdefault(self.pos, self)

    @property
    def is_empty(self):
        return isinstance(self.pos, Empty)

    @property
    def is_pass(self):
        return self.pos == Empty.PASS

    @property
    def is_root(self):
        return self.pos == Empty.FIRST_MOVE

    def real_children(self):
        return {k: v for (k, v) in self.children.values() if not v.is_empty}

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
