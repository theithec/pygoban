from . import board, move


class Event:
    pass


class MovePlayed(Event):
    def __init__(self, result: board.MoveResult):
        self.result = result

    def __str__(self):
        return f"Move Played: {self.result}"


class CursorChanged(Event):
    def __init__(self, result: board.MoveResult, board: board.Board):
        self.result = result
        self.board = board

    def __str__(self):
        return f"Cursor changed: {self.result}"


class MovesReseted(Event):
    def __init__(self, root: move.Move):
        self.root = root

    def __str__(self):
        return f"Move reseted: {self.root}"
