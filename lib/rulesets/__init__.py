from lib import EMPTY


class RuleViolation(Exception):
    pass


class KoViolation(RuleViolation):
    pass


class OccupiedViolation(RuleViolation):
    pass


class BaseRuleset:
    def __init__(self, game):
        self.ko = None
        self.game = game

    def validate(self, result):
        if self.game.movetree.board[result.x][result.y] != EMPTY:
            raise OccupiedViolation("Not empty:", result)

        elif (result.x, result.y) == self.ko:
            raise KoViolation

        elif result.libs == 1 and len(result.killed) == 1:
            for ko in result.killed:
                self.ko = ko
        else:
            self.ko = None
