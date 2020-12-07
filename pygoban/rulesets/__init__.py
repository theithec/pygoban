from pygoban.status import (
    EMPTY,
    BLACK,
    WHITE,
    WHITE_LIB,
    BLACK_LIB,
    DEAD_BLACK,
    DEAD_WHITE,
)
from pygoban import GameResult


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

        if not self.game.nextcolor == result.move.color:
            raise RuleViolation(
                "Wrong player %s %s"
                % (str(result.move.color), str(self.game.nextcolor))
            )

        x, y = result.move.pos
        bxy = self.game.board[x][y]
        if bxy != EMPTY:
            raise OccupiedViolation(f"Not empty: {result} BUT {bxy}")
        if not result.libs and not result.killed and not result.extra == "pass":
            raise NoLibsViolation(f"No liberties: {result}")

        if (x, y) == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if result.libs == 1 and len(result.killed) == 1:
            self.ko = list(result.killed)[0]
        else:
            self.ko = None

    def set_result(self, groups=None):
        blibs = 0
        wlibs = 0
        blibs = 0
        wlibs = 0
        wdead = self.game.prisoners[BLACK]
        bdead = self.game.prisoners[WHITE]
        if groups:
            board = self.game.board
            boardrange = range(board.boardsize)
            for x in boardrange:
                for y in boardrange:
                    status = board[x][y]
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

        return GameResult(
            points={BLACK: blibs, WHITE: wlibs}, prisoners={BLACK: wdead, WHITE: bdead}
        )
