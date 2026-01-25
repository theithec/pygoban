from dataclasses import dataclass, field
from typing import Any, Optional

from .board import Board, Color, Marker, Pos


@dataclass
class Annotations:  # pylint: disable=too-many-instance-attributes
    chars: dict[Pos, str] = field(default_factory=dict)
    numbers: dict[Pos, str] = field(default_factory=dict)
    markers: dict[Pos, Marker] = field(default_factory=dict)
    stones: dict[Pos, Color] = field(default_factory=dict)
    owned: dict[Pos, Color] = field(default_factory=dict)
    winrates: dict[Pos, str] = field(default_factory=dict)
    comment: str = ""
    time_left: int = 0
    stones_left: int = 0
    periods_left: int = 0
    progress: dict[Pos, Any] = field(default_factory=dict)
    infos: dict[str, str] = field(default_factory=dict)
    arrows: list[tuple[Pos, Pos]] = field(default_factory=list)
    lines: list[tuple[Pos, Pos]] = field(default_factory=list)


class Node:
    def __init__(
        self,
        color: Color,
        pos: Optional[Pos] = None,
        parent: Optional["Node"] = None,
    ) -> None:
        self.color = color
        self.pos = pos
        self.children: list["Node"] = []
        self.annos = Annotations()
        self.set_parent(parent)
        self.is_pass = self.color and self.parent and not self.pos
        self.is_root = not any([self.color, self.pos, self.parent])

    def set_parent(self, parent: Optional["Node"]):
        self.parent = parent
        if parent and self not in parent.children:
            parent.children.append(self)

    def _full_path(self) -> list["Node"]:
        path = []
        curr: Optional[Node] = self
        while curr:
            path.append(curr)
            curr = curr.parent
        path.reverse()
        return path

    def path(self) -> list["Node"]:
        return self._full_path()[1:]

    def full_path_to_last(self):
        path = self._full_path()
        node = self
        while node:
            if node := node.children[-1] if node.children else None:
                path.append(node)
        return path

    def root(self) -> "Node":
        return self._full_path()[0]

    def apply_permanent_annos(self, board: Board):
        for pos, color in self.annos.stones.items():
            board.intersection(pos, color)

    def __str__(self):
        return (
            f"Node {self.color}: {self.pos} / {len(self.path())}"
            f"C[{self.annos.comment[: (min(4, len(self.annos.comment) - 1))]}]"
        )

    def __repr__(self):
        return self.__str__()
        # return self if not self.parent else self.path()[0].parent

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False

        cmprs = [
            (self.parent, other.parent),
            (self.pos, other.pos),
            (self.color, other.color),
        ]
        return not any(sval != oval for (sval, oval) in cmprs)

    def __del__(self):
        if self.parent and self in self.parent.children:
            del self.parent.children[self.parent.children.index(self)]
        del self

    def as_copy(self) -> "Node":
        pos = Pos(*self.pos) if self.pos else None
        move: "Node" = self.__class__(color=self.color, pos=pos)
        move.annos = Annotations(**vars(self.annos))
        for child in self.children:
            child_cpy = child.as_copy()
            move.children.append(child_cpy)
            child_cpy.parent = move
        return move
