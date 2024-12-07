from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple, Union

from .board import Board, Color, Pos
from .info import GameInfo
from .results import ActionResult, ActionType, ColorResult, GameResult
from .stonescontroller import StonesController
from .timesettings import TimeSettings

# from .timesettings import TimeSettings


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
    coords: Set[Pos] = field(default_factory=set)


PosSetByColor = Dict[Color, Set[Pos]]
IntByColor = Dict[Color, int]


class Counter:
    def __init__(self, board: Board):
        self.board = board
        self.checked: Set[Pos] = set()

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

    def result(self) -> Tuple[PosSetByColor, IntByColor]:
        self.checked = set()
        empties: PosSetByColor = {Color.BLACK: set(), Color.WHITE: set()}
        deadonboard: IntByColor = {Color.BLACK: 0, Color.WHITE: 0}
        boardrange = range(self.board.boardsize)
        for x in boardrange:
            for y in boardrange:
                pos = Pos(x, y)
                inter = self.board.intersection(pos)
                if pos not in self.checked and inter.is_empty():
                    group = self.check(pos)
                    if group.owner and group.coords:
                        empties[group.owner].update(group.coords)
                if inter.owner and inter.owner != inter.color:
                    if inter.color:
                        deadonboard[inter.color] += 1

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
        self.stones: Optional[StonesController] = None
        self.info: GameInfo = info
        self.timesettings = timesettings
        # if timesettings:
        #     print("Timesettings", timesettings)

    def set_stonescontroller(self, stones: StonesController) -> "Ruleset":
        self.stones = stones
        return self

    def count(self, board: Board) -> ActionResult:
        assert self.stones
        counter = Counter(board)
        owned_empties, dob = counter.result()
        black_result = ColorResult(
            coords=owned_empties[Color.BLACK],
            killed=dob[Color.WHITE] + self.stones.dead[Color.WHITE],
        )
        white_result = ColorResult(
            coords=owned_empties[Color.WHITE],
            killed=dob[Color.BLACK] + self.stones.dead[Color.BLACK],
        )
        white_plus_komi = white_result.total() + float(self.komi)
        wbdiff = white_plus_komi - black_result.total()
        for col in (Color.BLACK, Color.WHITE):
            for empty in owned_empties[col]:
                board.intersection(empty).owner = col
        if wbdiff < 0:
            winner = Color.BLACK
            wbdiff = wbdiff * -1
        elif wbdiff > 0:
            winner = Color.WHITE
        else:
            winner = Color.EMPTY
        return ActionResult(
            type=ActionType.COUNT,
            board=self.stones.board,
            game_result=GameResult(
                winner=winner,
                reason=f"{winner}+{wbdiff}",
            ),
        )

    def validate_result(self, result: ActionResult) -> ActionResult:
        assert result.stone_result
        stone = result.stone_result.stone
        if stone.pos:
            self.passed = 0
        else:
            self.passed += 1
            if self.passed == 3:
                raise ThreePasses()
            return result
        assert stone.pos
        if stone.color.is_empty():
            return result
        assert self.stones
        color = self.stones.board.intersection(stone.pos).color
        if not color.is_empty():
            raise OccupiedViolation(f"Not empty: {result} BUT {color}")
        if not result.stone_result.libs and not result.stone_result.killed:
            raise NoLibsViolation(f"No liberties: {result}")
        if stone.pos == self.ko:
            raise KoViolation(f"Invalid Ko: {result}")
        if (
            len(result.stone_result.libs) == 1
            and result.stone_result.libs == result.stone_result.killed
        ):
            self.ko = list(result.stone_result.killed)[0]
        else:
            self.ko = None
        return result
