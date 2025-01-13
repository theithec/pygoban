from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from .board import Board, Color, Marker, Pos


@dataclass
class Annotations:
    chars: dict[Pos, str] = field(default_factory=dict)
    numbers: dict[Pos, str] = field(default_factory=dict)
    markers: dict[Pos, Marker] = field(default_factory=dict)
    stones: dict[Pos, Color] = field(default_factory=dict)
    owned: dict[Pos, Color] = field(default_factory=dict)
    winrates: dict[Pos, str] = field(default_factory=dict)
    comment: str = ""
    time_left: dict[Color, int] = field(default_factory=dict)
    stones_left: dict[Color, int] = field(default_factory=dict)
    byoyomi_left: dict[Color, int] = field(default_factory=dict)
    progress: dict[Pos, Any] = field(default_factory=dict)
    infos: dict[str, str] = field(default_factory=dict)


class Node:
    def __init__(
        self,
        color: Color,
        pos: Optional[Pos] = None,
        parent: Optional["Node"] = None,
    ):
        self.color = color
        self.pos = pos
        self.children: List["Node"] = []
        self.annos = Annotations()
        self.set_parent(parent)
        self.is_pass = self.color and self.parent and not self.pos
        self.is_root = not any([self.color, self.pos, self.parent])

    def set_parent(self, parent: Optional["Node"]):
        if parent and self not in parent.children:
            parent.children.append(self)
        self.parent = parent

    def _full_path(self) -> List["Node"]:
        path = []
        curr: Optional[Node] = self
        while curr:
            path.append(curr)
            curr = curr.parent
        path.reverse()
        return path

    def path(self) -> List["Node"]:
        return self._full_path()[1:]

    def root(self) -> "Node":
        return self._full_path()[0]

    def apply_permanent_annos(self, board: Board):
        for pos, color in self.annos.stones.items():
            board.intersection(pos, color)

    def __str__(self):
        return (
            f"Stone {self.color}: {self.pos} / {len(self.path())}"
            f"C[{self.annos.comment[:(min(4, len(self.annos.comment) - 1))]}]"
        )

    def __repr__(self):
        return self.__str__()
        # return self if not self.parent else self.path()[0].parent

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        cmprs = [(self.pos, other.pos), (self.color, other.color)]
        # TODO: use parent?
        if not any((self.pos, self.color, other.pos, other.color)):
            cmprs.append((self.annos, other.annos))
            return self.annos == other.annos
        return not any(sval != oval for (sval, oval) in cmprs)

    def _as_copy(
        self, target: "Node", found: Optional["Node"] = None
    ) -> Tuple["Node", Optional["Node"]]:
        pos = Pos(*self.pos) if self.pos else None
        move: "Node" = self.__class__(color=self.color, pos=pos)
        move.annos = Annotations(**vars(self.annos))
        for child in self.children:
            child_cpy, found = child._as_copy(target=target, found=found)
            move.children.append(child_cpy)
            child_cpy.parent = move
            if target == child:
                found = child_cpy
        return (
            move,
            found,
        )

    def as_copy(self):
        """start with root!"""
        path = self.path()
        root = self if not self.parent else path[0].parent
        assert root
        rcpy = root._as_copy(target=self)
        # print("RCOPY", rcpy)
        return rcpy[1]
