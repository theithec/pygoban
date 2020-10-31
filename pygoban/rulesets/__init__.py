from pygoban.status import EMPTY


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
                "Wrong player %s %s" % (str(result.color), str(self.game.currentcolor)))

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
