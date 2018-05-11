from . import STATUS, BLACK, WHITE
from .movetree import MoveTree
from .rulesets import RuleViolation


class Observer:
    def __init__(self, game):
        self.game = game

    def set_turn(self, col_id):
        self.game.players[col_id].set_turn(True)
        self.game.otherplayer(col_id).set_turn(False)

    def handle_exception(self, exception):
        print(exception)
        raise(exception)


class ConsoleObserver(Observer):

    def set_turn(self, col_id):
        super().set_turn(col_id)
        print(self.game.movetree.board)
        print(self.game.movetree.prisoners)
        print("Has turn", STATUS[col_id])


class Game:

    def __init__(self, boardsize, black, white,
                 ruleset_cls=None, observer_cls=None):
        self.movetree = MoveTree(boardsize)
        self.players = {
            BLACK: black,
            WHITE: white
        }
        self.__currentcolor = self.firstplayer().col_id
        observer_cls = observer_cls or ConsoleObserver
        self.ruleset = ruleset_cls(self) if ruleset_cls else None
        self.observer = observer_cls(self)

    @property
    def currentcolor(self):
        return self.__currentcolor

    @currentcolor.setter
    def currentcolor(self, col_id):
        self.__currentcolor = col_id
        self.observer.set_turn(col_id)


    def player(self, color=None):
        color = color or self.currentcolor
        return self.players[color]

    def otherplayer(self, color=None):
        color = color or self.currentcolor
        return self.players[BLACK if color == WHITE else WHITE]

    def firstplayer(self):
        return self.players[BLACK]

    def play(self, col_id, x, y):
        if not self.currentcolor == col_id:
            raise RuleViolation("Wrong player")

        result = self.movetree.test_move(col_id, x, y)
        if self.ruleset:
            try:
                self.ruleset.validate(result)
            except RuleViolation as e:
                self.observer.handle_exception(e)
                return

        self.movetree.apply_result(result)
        self.currentcolor = self.otherplayer().col_id

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.set_cursor(parent)
        self.currentcolor = self.otherplayer(parent.col_id).col_id
        self.observer.set_turn(self.currentcolor)
