from . import STATUS, BLACK, WHITE
from .movetree import MoveTree
from .rulesets import RuleViolation
from .observer import ConsoleObserver
from .board import default_result


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
        for player in self.players.values():
            player.set_game(self)

        self.set_currentcolor(self.firstplayer().col_id)


    @property
    def currentcolor(self):
        return self.__currentcolor

    # @currentcolor.setter
    # def currentcolor(self, col_id):
    #     #import pdb; pdb.set_trace()
    #     self.__currentcolor = col_id
    #     self.observer.set_turn(col_id)

    def set_currentcolor(self, col_id, result=None):
        self.__currentcolor = col_id
        self.observer.set_turn(col_id, result)


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
                self.set_currentcolor(col_id)
            else:
                self.movetree.apply_result(result)
                self.set_currentcolor(self.otherplayer().col_id, result)

    def undo(self):
        parent = self.movetree.cursor.parent
        self.movetree.set_cursor(parent)
        self.set_currentcolor(
            self.otherplayer(parent.col_id).col_id,
            default_result._replace(extra="undo"))

    def sgf_coords(self, x, y):
        return "%s%s" % (chr(65+x), y+1)

    def array_indexes(self, coords):
        return (ord(coords[0])-65, int(coords[1])-1)
