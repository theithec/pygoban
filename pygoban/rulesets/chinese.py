from pygoban.board import Board, Color, Pos

from . import BaseCounting, BaseRuleset, FloatByColor, Key, PosSetByColor, by_key


class ChineseCounting(BaseCounting):
    def __init__(self, board: Board) -> None:
        super().__init__(board=board)
        self.owned = {Color.BLACK: set(), Color.WHITE: set()}

    def result(self) -> (PosSetByColor, FloatByColor):
        boardrange = range(self.board.boardsize)

        for x in boardrange:
            for y in boardrange:
                inter = self.board[x][y]
                if inter.is_empty():
                    continue
                inter.owner = inter.color

        # empties: PosSetByColor = {Color.BLACK: set(), Color.WHITE: set()}
        for x in boardrange:
            for y in boardrange:
                pos = Pos(x, y)
                inter = self.board.intersection(pos)
                if pos in self.checked:
                    continue
                if inter.is_empty():
                    group = self.check(pos)

        for x in boardrange:
            for y in boardrange:
                inter = self.board[x][y]
                if inter.owner:
                    self.owned[inter.owner].add(Pos(x, y))

        # breakpoint()

        return (self.owned, {Color.BLACK: 0, Color.WHITE: 0})

    def toggle_status(self, pos):
        inter = self.board.intersection(pos)
        if inter.color.is_empty():
            return
        chain = self.board.get_chain(pos)
        owner = inter.color.other()
        for cpos in chain:
            inter = self.board.intersection(cpos)
            inter.owner = owner


class ChineseRuleset(BaseRuleset):
    name = Key.CHINESE.name.capitalize()
    CounterCls = ChineseCounting

    def count(self):
        pass


by_key[Key.CHINESE] = ChineseRuleset
