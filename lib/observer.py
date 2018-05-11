from . import STATUS  # , BLACK, WHITE


class Observer:
    def __init__(self, game):
        self.game = game

    def set_turn(self, col_id, result):
        self.game.players[col_id].set_turn(True, result)
        self.game.otherplayer(col_id).set_turn(False, result)

    def handle_exception(self, exception):
        print(exception)
        raise(exception)


class ConsoleObserver(Observer):

    def set_turn(self, col_id, result):
        print(self.game.movetree.board)
        print(self.game.movetree.prisoners)
        print("Has turn", STATUS[col_id])

        super().set_turn(col_id, result)
