from dataclasses import dataclass
from typing import Tuple

from pygoban.board import Color, Pos

from . import (
    BaseColorResult,
    BaseCounting,
    BaseRuleset,
    FloatByColor,
    Key,
    PosSetByColor,
    by_key,
)


@dataclass
class ColorResult(BaseColorResult):
    """Result after counting"""

    prisoners: int = 0

    def __post_init__(self):
        self._summands = ["points", "prisoners", "komi"]


class JapaneseCounting(BaseCounting):
    def result(self) -> Tuple[PosSetByColor, FloatByColor]:
        self.checked = set()
        empties: PosSetByColor = {Color.BLACK: set(), Color.WHITE: set()}
        deadonboard: FloatByColor = {Color.BLACK: 0, Color.WHITE: 0}
        for pos, inter in self.board.iter():
            if pos in self.checked:
                continue
            if inter.is_empty():
                group = self.check(pos)
                if group.owner and group.coords:
                    empties[group.owner].update(group.coords)
            else:
                if inter.owner and inter.owner != inter.color:
                    deadonboard[inter.color] += 1
                    if group.owner:
                        empties[inter.owner].add(pos)

        return empties, deadonboard

    def toggle_status(self, pos):
        chain = self.board.get_chain(pos)
        inter = self.board.intersection(pos)
        owner = (
            None
            if inter.owner
            else (Color.BLACK if inter.color == Color.WHITE else Color.WHITE)
        )
        for cpos in chain:
            inter = self.board.intersection(cpos)
            inter.owner = owner


class JapaneseRuleset(BaseRuleset):
    name = Key.JAPANESE.name.capitalize()
    _CounterCls = JapaneseCounting

    def count(self) -> dict[str, ColorResult]:
        assert self.nodes
        counter = JapaneseCounting(self.nodes.board)
        coords, deadonboard = counter.result()

        return {
            Color.BLACK.name.lower(): ColorResult(
                prisoners=int(deadonboard[Color.WHITE])
                + self.nodes.total_dead[Color.WHITE],
                owned=coords[Color.BLACK],
                komi=None,
            ),
            Color.WHITE.name.lower(): ColorResult(
                prisoners=int(deadonboard[Color.BLACK])
                + self.nodes.total_dead[Color.BLACK],
                owned=coords[Color.WHITE],
                komi=self.komi,
            ),
        }

    def toggle_status(self, pos: Pos):
        assert self.nodes
        counter = JapaneseCounting(self.nodes.board)
        counter.toggle_status(pos)
        return self.count()


by_key[Key.JAPANESE] = JapaneseRuleset
