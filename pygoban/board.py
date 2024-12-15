"""The board and helpers """

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Set, Tuple

from . import coords


class Color(IntEnum):
    """The 'color' of an intersection (and of 'stone.Stone)'"""

    EMPTY = 0
    BLACK = 1
    WHITE = 2

    def short(self):
        return str(self.name)[0]

    def is_empty(self):
        return self == self.EMPTY

    def __str__(self):
        return str(self.name)[0]

    def other(self):
        assert not self.is_empty()
        return self.WHITE if self.name == "BLACK" else self.BLACK


class Marker(Enum):
    """Marker for a `stone.Stone`, lives here for easier importing"""

    TR = "triangle"
    CR = "circle"
    SQ = "square"
    NR = "number"
    MA = "x"
    OWNED = "owned"
    DIMMED = "dimmed"


class Pos(tuple):
    """A handcrafted named tuple"""

    def __new__(cls, x, y):
        return super().__new__(cls, (x, y))

    def __init__(self, *_args, **_kwargs):
        self.x = self[0]
        self.y = self[1]


@dataclass
class Intersection:
    """A 'value' on a go board"""

    color: Color
    owner: Optional[Color] = None

    def is_empty(self):
        return self.color.is_empty()


class Board(List[List[Intersection]]):
    """A Go board as a two dimensional list of intersections"""

    def __init__(self, boardsize: int):
        super().__init__()
        self.boardrange = range(boardsize)
        self.extend(
            [[Intersection(color=Color.EMPTY) for _x in self.boardrange] for _y in self.boardrange]
        )
        self.boardsize = boardsize

    def get_chain(self, pos: Pos, chain: Optional[Set[Pos]] = None):
        """Return the chain of stones for a given position"""
        inter = self.intersection(pos)
        assert inter.color
        chain = chain or set()
        chain.add(pos)
        for adj_pos in self.adjacent_ins(pos):
            adj_inter = self.intersection(adj_pos)
            if adj_inter.color == inter.color and adj_pos not in chain:
                self.get_chain(adj_pos, chain)
        return chain

    def adjacent_ins(self, index) -> Dict[Pos, Intersection]:
        """Return the 'neighbours' of a position"""
        adjacents = {}
        x, y = index
        if x > 0:
            adjacents[Pos(x - 1, y)] = self[x - 1][y]

        if x < self.boardsize - 1:
            adjacents[Pos(x + 1, y)] = self[x + 1][y]

        if y > 0:
            adjacents[Pos(x, y - 1)] = self[x][y - 1]

        if y < self.boardsize - 1:
            adjacents[Pos(x, y + 1)] = self[x][y + 1]

        return adjacents

    def _analyze(
        self,
        pos: Pos,
        started: Optional[Set[Pos]] = None,
        group: Set[Pos] | None = None,
        killed: Set[Pos] | None = None,
        libs: Set[Pos] | None = None,
        findkilled: bool = True,
    ) -> Tuple[Set[Pos], Set[Pos], Set[Pos], Set[Pos], bool]:
        """Return the analyze a stone (pos, already played)"""
        started = started or set()
        group = group or set()
        killed = killed or set()
        libs = libs or set()
        started.add(pos)
        group.add(pos)
        adjacents = self.adjacent_ins(pos)
        for axy, inter in adjacents.items():
            if axy in started:
                continue

            # a liberty
            if inter.is_empty():
                started.add(axy)
                libs.add(Pos(*axy))

            # friend
            elif inter == self[pos[0]][pos[1]]:
                started, group, killed, libs = self._analyze(
                    axy,
                    started=started,
                    group=group,
                    killed=killed,
                    libs=libs,
                    findkilled=False,
                )[:4]

            # enemy!
            elif findkilled:
                result = self._analyze(axy, findkilled=False)
                enemylibs = result[3]
                # print("enemylibs", enemylibs)
                if not enemylibs:
                    enemygroup = result[1]
                    killed |= enemygroup
                    started |= enemygroup
                    killed_adjacents = enemygroup & set(adjacents)
                    libs |= killed_adjacents

        return started, group, killed, libs, findkilled

    def analyze(self, pos: Pos, findkilled: bool = True):
        """Return the finished analyze of a played stone"""
        _started, _group, killed, libs, _findkilled = self._analyze(pos=pos, findkilled=findkilled)
        return killed, libs

    def intersection(
        self, pos: Pos, status: Optional[Color] = None, owner: Optional[Color] = None
    ) -> Intersection:
        """Return the `Intersection`(holding the value) of a `Pos`"""
        x, y = pos
        if status is not None:
            self[x][y].color = status

        if owner is not None:
            self[x][y].owner = owner
        return self[x][y]

    def __str__(self):
        return "BOARD"
        cpy = self  # .rotated(switch_axis=False, switch_y=False)
        txt = "\n    "
        txt += " ".join([coords.letter_from_int(i) for i in range(cpy.boardsize)])

        txt += "\n\n"
        for xorg in range(cpy.boardsize):
            x = cpy.boardsize - xorg - 1
            txt += "%2s  " % (x + 1)
            txt += " ".join(
                [cpy.intersection(Pos(y, xorg)).color.short() for y in range(cpy.boardsize)]
            )
            txt += "\n"

        return txt

    def __repr__(self):
        size = str(len(self))
        return "x".join((size,) * 2)

    # def rotated(self, switch_axis=False, switch_x=False, switch_y=False):
    #     if not any((switch_axis, switch_x, switch_y)):
    #         return self

    #     cpy = deepcopy(self)
    #     boardrange = range(self.boardsize)
    #     if switch_axis:
    #         for x in boardrange:
    #             for y in boardrange:
    #                 cpy[x][y] = self[y][x]

    #     if switch_x:
    #         cpy.reverse()

    #     if switch_y:
    #         for x in boardrange:
    #             cpy[x].reverse()

    #     return cpy
