from . import BLACK, WHITE
from .move import Move
from .board import Board
from .rulesets import RuleViolation


class MoveTree:

    def __init__(self, boardsize, ruleset=None):
        self.board = Board(boardsize)
        self.ruleset = ruleset
        self.root = Move(None)
        self.refresh(self.root)

    def add(self, col_id, x, y, parent=None):
        oldcursor = self.cursor
        self.cursor = parent or self.cursor

        if parent and parent != self.cursor:
            self.refresh(parent)

        result = self.board.result(col_id, x, y, do_apply=False)
        if self.ruleset:
            try:
                self.ruleset.validate(result)
            except RuleViolation as e:
                self.refresh(oldcursor)
                raise e

        self.board.apply_result(result)
        self.prisoners[col_id] += len(result['killed'])
        self.cursor = Move(col_id, x, y, self.cursor)
        return result

    def get_path(self):
        path = []
        curr = self.cursor
        while curr:
            path.append(curr)
            curr = curr.parent

        path.reverse()
        return path

    def refresh(self, move):
        self.cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        path = self.get_path()
        self.board = Board(self.board.boardsize)

        for move in path:
            if not move.is_pass:
                self.add(move.col_id, move.x, move.y)
