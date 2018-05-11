'''Boards'''

from copy import deepcopy
from collections import  namedtuple

from . import (
        EMPTY, BLACK, WHITE, KO, DEAD_BLACK, DEAD_WHITE)


Result2 = namedtuple('Result', ['x', 'y', 'col_id', 'libs', 'killed', 'group', 'extra'])

default_result = Result2(-1, -1, None, None, None, None, None)

class Board(list):
    """
        A situation in a go game/movetree
    """

    def __init__(self, boardsize, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for x in range(boardsize):
            self.append([])
            for y in range(boardsize):
                self[x].append(EMPTY)
        self.boardsize = boardsize

    def _adjacent_ins(self, index):

        adjacents = {}
        x, y = index
        if x > 0:
            adjacents[(x-1, y)] = self[x-1][y]

        if x < self.boardsize-1:
            adjacents[(x+1, y)] = self[x+1][y]

        if y > 0:
            adjacents[(x, y-1)] = self[x][y-1]

        if y < self.boardsize-1:
            adjacents[(x, y+1)] = self[x][y+1]

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
            if acol < 1:
                started.add(axy)
                libs += 1

            # friend
            elif acol == col:
                started, group, killed, libs = self.analyze(
                    axy[0], axy[1], started=started, group=group, killed=killed,
                    libs=libs, findkilled=False)[:4]

            # enemy!
            elif findkilled:
                result = self.analyze(axy[0], axy[1], findkilled=False)
                ogroup = result[1]
                olibs = result[3]
                if olibs == 0:
                    killed |= ogroup
                    started |= ogroup
                    killed_adjacents = ogroup & set(adjacents)
                    libs += len(killed_adjacents)

        return started, group, killed, libs, findkilled

    def result(self, col_id, x, y, do_apply=True):
        '''Result of a move (may be invalid)'''
        cpy = deepcopy(self)
        cpy[x][y] = col_id
        raw = cpy.analyze(x, y)
        result = default_result._replace(
            col_id=col_id,
            x=x,
            y=y,
            group=raw[1],
            killed=raw[2],
            libs=raw[3]
        )
        if do_apply:
            self.apply_result(result)

        return result

    def apply_result(self, result):
        r = result
        self[r.x][r.y] = r.col_id
        for x, y in r.killed:
            self[x][y] = EMPTY

    def __str__(self):
        legend = {
            BLACK: "B",
            WHITE: "W",
            DEAD_BLACK: "b",
            DEAD_WHITE: "w",
            KO: "?",
            EMPTY: "+",
        }
        txt = "\n    "
        txt += " ".join([chr(65 + i) for i in range(self.boardsize)])
        txt += "\n\n"
        for i, x in enumerate(range(self.boardsize)):
            txt += "%2s  " % (i+1)
            txt += " ".join(
                ["%s" % legend[self[x][y]]
                    for y in range(self.boardsize)])

            txt += "\n"

        return txt
