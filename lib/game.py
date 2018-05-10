from . import STATUS, BLACK, WHITE
from .movetree import MoveTree
from .rulesets import RuleViolation


class Player():
    def __init__(self, col_id, name=None, game=None):
        self.col_id = col_id
        self.name = name or STATUS[col_id]
        self.game = game or None
        if self.game:
            self.game.players[col_id] = self
        self.has_turn = False

    def play(self, x, y):
        self.game.play(self.col_id, x, y)

    def set_turn(self, has_turn):
        pass


class Observer:
    def __init__(self, game):
        self.game = game

    def set_turn(self, col_id):
        self.game.players[col_id].set_turn(True)
        self.game.otherplayer(col_id).set_turn(False)


class ConsoleObserver(Observer):

    def set_turn(self, col_id):
        super().set_turn(col_id)
        print(self.game.movetree.board)
        print(self.game.movetree.prisoners)
        print("Has turn", STATUS[col_id])


class Game:

    def __init__(self, boardsize, black, white,
                 ruleset=None, observer_cls=None):
        self.movetree = MoveTree(boardsize, ruleset)
        self.players = {
            BLACK: black,
            WHITE: white
        }
        self.currentcolor = self.firstplayer().col_id
        observer_cls = observer_cls or ConsoleObserver
        self.observer = observer_cls(self)

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

        try:
            self.movetree.add(col_id, x, y)
        except RuleViolation as e:
            print(e)
        else:
            othercolor = self.otherplayer().col_id
            self.observer.set_turn(othercolor)
            self.currentcolor = othercolor

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.refresh(parent)
        self.currentcolor = self.otherplayer(parent.col_id).col_id
        self.observer.set_turn(self.currentcolor)
