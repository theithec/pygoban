from dataclasses import dataclass, field
from enum import StrEnum
from functools import reduce
from typing import Generator, Optional, Type, Union

from ..board import Board, Color, Pos
from ..info import GameInfo
from ..nodescontroller import NodesController
from ..results import Event, TurnDone
from ..timesettings import TimeSettings


class Key(StrEnum):
    CHINESE = "Chinese"
    JAPANESE = "Japanse"


class WrongColor(Exception):
    pass


class RuleViolation(Exception):
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


@dataclass
class BaseColorResult(Event):
    """_summands: tuple must be defined in subclasses"""

    owned: set[Pos]
    komi: float | None

    def __post_init__(self):
        self._summands = []

    @property
    def points(self) -> int:
        return len(self.owned)

    def summands(self) -> Generator[tuple, None, None]:
        for summand in self._summands:
            if (val := getattr(self, summand)) is None:
                continue
            yield summand, val

    @property
    def total(self):
        total = 0
        for _, val in self.summands():
            total += val
        total2 = reduce(lambda x, y: x + y[1], self.summands(), 0)
        assert total == total2
        return total


PosSetByColor = dict[Color, set[Pos]]
FloatByColor = dict[Color, float]


class BaseCounting:
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

    def toggle_status(self, pos):
        raise NotImplementedError

    def result(self):
        raise NotImplementedError


class BaseRuleset:
    name = "default"
    _CounterCls: Type[BaseCounting]

    def __init__(
        self,
        boardsize: int,
        komi: float,
        handicap: int,
        info: GameInfo,
        first: Color = Color.BLACK,
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

    def set_node_controller(self, nodes: NodesController) -> "BaseRuleset":
        self.nodes = nodes
        return self

    def validate_result(self, result: TurnDone) -> TurnDone:
        node = result.node
        if node.pos:
            self.passed = 0
        else:
            self.passed += 1
            if self.passed == 3:
                self.passed = 0
                raise ThreePasses()
            return result
        assert node.pos
        if node.color.is_empty():
            return result
        assert self.nodes
        color = self.nodes.board.intersection(node.pos).color
        if not color.is_empty():
            raise OccupiedViolation(f"Not empty: {result} BUT {color}")
        if not result.libs and not result.killed:
            raise NoLibsViolation(f"No liberties: {result}")
        if node.pos == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if (
            len(result.libs) == 1
            and result.libs == result.killed
            and len(result.board.get_chain(node.pos)) == 1
        ):
            self.ko = list(result.killed)[0]
        else:
            self.ko = None
        return result

    def count(self):
        raise NotImplementedError

    def toggle_status(self, pos: Pos):
        raise NotImplementedError


by_key: dict[Key, Type[BaseRuleset]] = {}
