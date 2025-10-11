from dataclasses import dataclass, field
from typing import Optional, Tuple, Union
from enum import StrEnum

from .board import Board, Color, Pos
from .info import GameInfo
from .results import TurnDone
from .nodescontroller import NodesController
from .timesettings import TimeSettings

# from .timesettings import TimeSettings


class Key(StrEnum):
    CHINESE = "Chinese"
    JAPANESE = "Japanse"


class RuleViolation(Exception):
    pass


class WrongColor(Exception):
    pass


class KoViolation(RuleViolation):
    pass


class OccupiedViolation(RuleViolation):
    pass


class NoLibsViolation(RuleViolation):
    pass


class ThreePasses(Exception):
    pass


@dataclass
class Group:
    owner: Optional[Union[Color, bool]] = None
    coords: set[Pos] = field(default_factory=set)


PosSetByColor = dict[Color, set[Pos]]
FloatByColor = dict[Color, float]


class Counter:
    def __init__(self, board: Board) -> None:
        self.board = board
        self.checked: set[Pos] = set()

    def check(self, pos: Pos, group: Optional[Group] = None):
        group = group or Group()
        group.coords.add(pos)
        self.checked.add(pos)
        for adj in self.board.adjacent_ins(pos):
            adj_inter = self.board.intersection(adj)
            if adj_inter.is_empty():
                if adj not in self.checked:
                    self.check(adj, group)
            else:
                val = adj_inter.owner or adj_inter.color
                if group.owner is None:
                    group.owner = val
                elif group.owner != val:
                    group.owner = False

        for coord in group.coords:
            self.board.intersection(coord).owner = group.owner
        return group

    def result(self) -> Tuple[PosSetByColor, FloatByColor]:
        self.checked = set()
        empties: PosSetByColor = {Color.BLACK: set(), Color.WHITE: set()}
        deadonboard: FloatByColor = {Color.BLACK: 0, Color.WHITE: 0}
        boardrange = range(self.board.boardsize)
        for x in boardrange:
            for y in boardrange:
                pos = Pos(x, y)
                inter = self.board.intersection(pos)
                if pos in self.checked:
                    continue
                if inter.is_empty():
                    group = self.check(pos)
                    if group.owner and group.coords:
                        empties[group.owner].update(group.coords)
                else:
                    group = Group()
                if inter.owner and inter.owner != inter.color:
                    if inter.color:
                        deadonboard[inter.color] += 1
                        if group.owner:
                            empties[group.owner].add(pos)

        return empties, deadonboard


class Ruleset:
    name = "default"

    def __init__(
        self,
        boardsize: int,
        komi: float,
        handicap: int,
        info: GameInfo,
        first: Color = Color.BLACK,
        # title: str,
        timesettings: TimeSettings | None = None,
    ):
        self.boardsize = boardsize
        self.komi = komi
        self.handicap = handicap
        self.ko: Optional[Pos] = None
        self.passed = 0
        self.first: Color = first
        self.nodes: Optional[NodesController] = None
        self.info: GameInfo = info
        self.timesettings = timesettings

    def set_node_controller(self, nodes: NodesController) -> "Ruleset":
        self.nodes = nodes
        return self

    def validate_result(self, result: TurnDone) -> TurnDone:
        stone = result.node
        if stone.pos:
            self.passed = 0
        else:
            self.passed += 1
            if self.passed == 3:
                self.passed = 0
                raise ThreePasses()
            return result
        assert stone.pos
        if stone.color.is_empty():
            return result
        assert self.nodes
        color = self.nodes.board.intersection(stone.pos).color
        if not color.is_empty():
            raise OccupiedViolation(f"Not empty: {result} BUT {color}")
        if not result.libs and not result.killed:
            raise NoLibsViolation(f"No liberties: {result}")
        if stone.pos == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if (
            len(result.libs) == 1
            and result.libs == result.killed
            and len(result.board.get_chain(stone.pos)) == 1
        ):
            self.ko = list(result.killed)[0]
        else:
            self.ko = None
        return result


class JapaneseRuleset(Ruleset):
    name = Key.JAPANESE.name.capitalize()
    CounterCls = Counter


class ChineseRuleset(Ruleset):
    name = Key.CHINESE.name.capitalize()
    CounterCls = Counter


by_key = {
    Key.CHINESE: ChineseRuleset,
    Key.JAPANESE: JapaneseRuleset,
}
