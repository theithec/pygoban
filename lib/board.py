'''Boards'''

import math

from .status import (
    EMPTY, BLACK, WHITE, KO, LONGSTRSTATUS, DEAD_BLACK, DEAD_WHITE)


class Board(list):
    """
        A situation in a go game/movetree
    """

    def __init__(self, boardsize=None, oldboard=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if boardsize:
            self.extend([EMPTY for index in range(boardsize**2)])
            self.prisoners = {
                BLACK: 0,
                WHITE: 0,
            }

        if oldboard:
            self.extend(oldboard)
            self.prisoners = oldboard.prisoners
            self.last_color = oldboard.last_color
        else:
            self.last_color = None

        self.boardsize = int(math.sqrt(len(self)))
        if boardsize:
            assert boardsize == self.boardsize

    def get_index(self, x, y):
        """index from x, y"""
        return (y*self.boardsize) + x

    def _adjacent_ins(self, index):
        adjacents = {}
        y, x = int(index / self.boardsize), int(index % self.boardsize)
        if x > 0:
            aindex = self.get_index(x-1, y)
            adjacents[aindex] = self[aindex]

        if x < self.boardsize-1:
            aindex = self.get_index(x+1, y)
            adjacents[aindex] = self[aindex]

        if y > 0:
            aindex = self.get_index(x, y-1)
            adjacents[aindex] = self[aindex]

        if y < self.boardsize-1:
            aindex = self.get_index(x, y+1)
            adjacents[aindex] = self[aindex]

        return adjacents

    def analyze(self, index, started=None, group=None, killed=None,
                libs=0, findkilled=True):
        '''Analyze from a starting point'''
        started = started or set()
        group = group or set()
        killed = killed or set()
        col = self[index]
        started.add(index)
        group.add(index)
        adjacents = self._adjacent_ins(index)
        for axy, acol in adjacents.items():
            # a liberty
            if acol < 1 and axy not in started:
                started.add(axy)
                libs += 1

            # friend
            if acol == col and axy not in started:
                started, group, killed, libs = self.analyze(
                    axy, started=started, group=group, killed=killed,
                    libs=libs, findkilled=False)[:4]

            # enemy!
            if findkilled and acol > 0 and acol != col and axy not in started:
                #  ostarted, ogroup, okilled, olibs, ofindkilled = self._move(
                result = self.analyze(axy, findkilled=False)
                ogroup = result[1]
                olibs = result[3]
                if olibs == 0:
                    killed |= ogroup
                    started |= ogroup
                    killed_adjacents = ogroup & set(adjacents)
                    libs += len(killed_adjacents)

        return started, group, killed, libs, findkilled

    def result(self, col_id, x, y):
        '''Result of a move (may be invalid)'''
        cpy = Board(
            oldboard=self
        )
        index = self.get_index(x, y)
        cpy[index] = col_id
        result = cpy.analyze(index)
        killed = result[2]
        cpy.prisoners = self.prisoners
        cpy.prisoners[col_id] += len(killed)
        for k in killed:
            cpy[k] = EMPTY

        return {
            'index': index,
            'board': cpy,
            'killed': killed,
            'group': result[1],
            'libs': result[3]
        }

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
            txt += "%2s  " % (self.boardsize - i)
            txt += " ".join(
                ["%s" % legend[self[(x*self.boardsize + y)]]
                 for y in range(self.boardsize)])
            txt += "\n"

        for color in (BLACK, WHITE):
            print("%s captured %s" % (
                LONGSTRSTATUS[color],
                self.prisoners[color],
            ))

            return txt
