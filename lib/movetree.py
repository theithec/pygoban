from . import BLACK, WHITE
from .move import Move
from .board import Board


class MoveTree:

    def __init__(self, boardsize):
        self.board = Board(boardsize)
        self.root = Move(None)
        self.set_cursor(self.root)

    def test_move(self, col_id, x, y, apply_result=False):
        result = self.board.result(col_id, x, y, do_apply=apply_result)
        if apply_result:
            self.apply_result(result)

        return result

    def apply_result(self, result, move=None):
        self.board.apply_result(result)
        col_id = result.col_id
        self.prisoners[col_id] += len(result.killed)
        self.cursor = move or Move(col_id, result.x, result.y, self.cursor)

    def get_path(self):
        path = []
        curr = self.cursor
        while curr:
            path.append(curr)
            curr = curr.parent

        path.reverse()
        return path

    def set_cursor(self, move):
        self.cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        path = self.get_path()
        print("PATH", [str(m) for m in path])
        self.board = Board(self.board.boardsize)

        for move in path:
            if not move.is_pass:
                result = self.test_move(move.col_id, move.x, move.y)
                self.apply_result(result, move)

