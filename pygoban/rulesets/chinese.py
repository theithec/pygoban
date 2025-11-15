from dataclasses import dataclass

from pygoban.board import Board, Color, Pos

from . import (
    BaseColorResult,
    BaseCounting,
    BaseRuleset,
    Key,
    by_key,
)


@dataclass
class ColorResult(BaseColorResult):
    """Result after counting"""

    def __post_init__(self):
        self._summands = ["points", "komi"]


class ChineseCounting(BaseCounting):
    def __init__(self, board: Board) -> None:
        super().__init__(board=board)
        self.owned: dict[Color, set] = {Color.BLACK: set(), Color.WHITE: set()}

    def result(self) -> dict[Color, set]:
        for _, inter in self.board.iter():
            if not (inter.is_empty() or inter.owner):
                inter.owner = inter.color

        for pos, inter in self.board.iter():
            if pos in self.checked:
                continue
            if inter.is_empty():
                self.check(pos)

        for pos, inter in self.board.iter():
            if inter.owner:
                self.owned[inter.owner].add(pos)

        return self.owned

    def toggle_status(self, pos):
        inter = self.board.intersection(pos)
        if inter.color.is_empty():
            return
        chain = self.board.get_chain(pos)
        owner = (inter.owner or inter.color).other()
        for cpos in chain:
            inter = self.board.intersection(cpos)
            inter.owner = owner


class ChineseRuleset(BaseRuleset):
    name = Key.CHINESE.name.capitalize()
    CounterCls = ChineseCounting

    def count(self) -> dict[str, ColorResult]:
        assert self.nodes
        counter = ChineseCounting(self.nodes.board)
        coords = counter.result()

        return {
            Color.BLACK.name.lower(): ColorResult(
                owned=coords[Color.BLACK],
                komi=None,
            ),
            Color.WHITE.name.lower(): ColorResult(
                owned=coords[Color.WHITE],
                komi=self.komi,
            ),
        }

    def toggle_status(self, pos: Pos):
        assert self.nodes
        counter = ChineseCounting(self.nodes.board)
        counter.toggle_status(pos)
        return self.count()


by_key[Key.CHINESE] = ChineseRuleset
