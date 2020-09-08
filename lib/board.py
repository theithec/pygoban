"""Boards"""
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set

from .status import EMPTY, Status
from .coords import letter_coord_from_int



class StonelessReason(Enum):
    UNDO = "undo"
    PASS = "pas"


@dataclass
class MoveResult:
    x: int
    y: int
    color: Status
    libs: Set[int] = field(default_factory=set)
    killed: Set[int] = field(default_factory=set)
    group: Set[int] = field(default_factory=set)
    extra: Optional[StonelessReason] = None


class StonelessResult(MoveResult):
    def __init__(self, color, extra):
        super().__init__(-1, -1, color, extra=extra)


class Board(list):
    """
        A situation in a go game/movetree
    """

    def __init__(self, boardsize):
        super().__init__()
        boardrange = range(boardsize)
        self.extend([[EMPTY for x in boardrange] for y in boardrange])
        self.boardsize = boardsize

    def _adjacent_ins(self, index):
        adjacents = {}
        x, y = index
        if x > 0:
            adjacents[(x - 1, y)] = self[x - 1][y]

        if x < self.boardsize - 1:
            adjacents[(x + 1, y)] = self[x + 1][y]

        if y > 0:
            adjacents[(x, y - 1)] = self[x][y - 1]

        if y < self.boardsize - 1:
            adjacents[(x, y + 1)] = self[x][y + 1]

        return adjacents

    def analyze(self, x, y, started=None, group=None, killed=None,
                libs=0, findkilled=True):
        '''Analyze from a starting point'''
        started = started or set()
        group = group or set()
        killed = killed or set()
        col = self[x][y]
        pos = (x, y)
        started.add(pos)
        group.add(pos)
        adjacents = self._adjacent_ins(pos)
        for axy, acol in adjacents.items():
            if axy in started:
                continue

            # a liberty
            if int(acol) < 1:
                started.add(axy)
                libs += 1

            # friend
            elif acol.intval == col.intval:
                started, group, killed, libs = self.analyze(
                    axy[0], axy[1], started=started, group=group, killed=killed,
                    libs=libs, findkilled=False)[:4]

            # enemy!
            elif findkilled:
                result = self.analyze(axy[0], axy[1], findkilled=False)
                enemylibs = result[3]
                if enemylibs == 0:
                    enemygroup = result[1]
                    killed |= enemygroup
                    started |= enemygroup
                    killed_adjacents = enemygroup & set(adjacents)
                    libs += len(killed_adjacents)

        return started, group, killed, libs, findkilled

    def result(self, color: Status, x, y):
        '''Result of a move (may be invalid)'''
        cpy = deepcopy(self)
        cpy[x][y] = color
        raw = cpy.analyze(x, y)
        result = MoveResult(
            x=x,
            y=y,
            color=color,
            libs=raw[3],
            killed=raw[2],
            group=raw[1]
        )
        return result

    def apply_result(self, result):
        self[result.x][result.y] = result.color
        for x, y in result.killed:
            self[x][y] = EMPTY

    def rotated(self, switch_axis=False, switch_x=False, switch_y=False):
        if not any((switch_axis, switch_x, switch_y)):
            return self

        cpy = deepcopy(self)
        boardrange = range(self.boardsize)
        if switch_axis:
            for x in boardrange:
                for y in boardrange:
                    cpy[x][y] = self[y][x]

        if switch_x:
            cpy.reverse()

        if switch_y:
            for x in boardrange:
                cpy[x].reverse()

        return cpy

    def __str__(self):
        cpy = self.rotated(switch_axis=False, switch_y=False)
        txt = "\n    "
        txt += " ".join([letter_coord_from_int(i, cpy.boardsize) for i in range(cpy.boardsize)])
        txt += "\n\n"
        for xorg in range(cpy.boardsize):
            x = cpy.boardsize - xorg - 1
            txt += "%2s  " % (x + 1)
            txt += " ".join([
                "%s" % (cpy[xorg][y]).short()
                for y in range(cpy.boardsize)])
            txt += "\n"

        return txt



