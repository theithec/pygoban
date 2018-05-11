from . import STATUS


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
