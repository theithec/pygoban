class Event:
    pass


class MovePlayed(Event):
    def __init__(self, result):
        self.result = result


class CursorChanged(Event):
    def __init__(self, move, board):
        self.move = move
        self.board = board
