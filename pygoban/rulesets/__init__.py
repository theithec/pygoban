from pygoban.status import (
    EMPTY,
    BLACK,
    WHITE,
    WHITE_LIB,
    BLACK_LIB,
    DEAD_BLACK,
    DEAD_WHITE,
)


class RuleViolation(Exception):
    pass


class KoViolation(RuleViolation):
    pass


class OccupiedViolation(RuleViolation):
    pass


class NoLibsViolation(RuleViolation):
    pass


class BaseRuleset:
    name = "Basic Rules"

    def __init__(self, game):
        self.ko = None
        self.game = game

    def validate(self, result):

        if not self.game.currentcolor == result.color:
            raise RuleViolation(
                "Wrong player %s %s" % (str(result.color), str(self.game.currentcolor))
            )

        bxy = self.game.board[result.x][result.y]
        if bxy != EMPTY:
            raise OccupiedViolation(f"Not empty: {result} BUT {bxy}")
        if not result.libs and not result.killed and not result.extra == "pass":
            raise NoLibsViolation(f"No liberties: {result}")

        if (result.x, result.y) == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if result.libs == 1 and len(result.killed) == 1:
            self.ko = list(result.killed)[0]
        else:
            self.ko = None

    def set_result(self, groups=None, end=None):
        if end:
            print("END", end)
        elif groups:
            blibs = 0
            wdead = self.game.prisoners[BLACK]
            wlibs = 0
            bdead = self.game.prisoners[WHITE]
            board = self.game.board
            boardrange = range(board.boardsize)
            for x in boardrange:
                for y in boardrange:
                    status = board[x][y]
                    print("XYS", x, y, int(status))
                    if status == BLACK_LIB:
                        blibs += 1
                    elif status == DEAD_WHITE:
                        blibs += 1
                        wdead += 1
                    elif status == WHITE_LIB:
                        wlibs += 1
                    elif status == DEAD_BLACK:
                        bdead += 1
                        wlibs += 1

            print("BWL", blibs, wlibs)
            print("BWD", bdead, wdead)
            print("I", self.game.infos)
            btotal = blibs + wdead
            wtotal = wlibs + bdead + float(self.game.infos["KM"])
            dif = abs(wtotal - btotal)
            print("RES: ", "B" if btotal > wtotal else "W", dif)
