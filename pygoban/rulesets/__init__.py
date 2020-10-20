from pygoban.status import EMPTY, KO


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
                "Wrong player %s %s", str(result.color), str(self.game.currentcolor))

        if result.extra == "pass":
            self.ko = None

        bxy = self.game._movetree.board[result.x][result.y]
        if bxy != EMPTY:
            raise OccupiedViolation(f"Not empty: {result} BUT {bxy}")
        if not result.libs and not result.killed:
            raise NoLibsViolation(f"No liberties: {result} BUT {bxy}")

        if (result.x, result.y) == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if result.libs == 1 and len(result.killed) == 1:
            self.ko = list(result.killed)[0]
            bxy = KO
        else:
            self.ko = None
