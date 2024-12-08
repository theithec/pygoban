import abc
from re import M
from threading import Thread
from typing import TYPE_CHECKING, List, Optional

# from .basecontroller import BaseGameControllerMixin
from .board import Marker
from .receivers import BaseReceiver
from .results import ActionResult, ActionType, ColorResult, GameResult, StoneResult
from .rulesets import Counter, Ruleset, RuleViolation, ThreePasses, WrongColor
from .stonescontroller import Color, Pos, Stone, StonesController

# if TYPE_CHECKING:
#     from .controller import GameController


class AbstractCallbacks(abc.ABC):
    @abc.abstractmethod
    def play(self, color: Color, pos: Optional[Pos] = None) -> None: ...

    @abc.abstractmethod
    def undo(self) -> None: ...

    @abc.abstractmethod
    def set_cursor(self, stone: Stone) -> None: ...

    @abc.abstractmethod
    def resign(self, color: Color) -> None: ...

    @abc.abstractmethod
    def start(self, receivers: List["BaseReceiver"], stone: Optional[Stone] = None) -> None: ...

    @abc.abstractmethod
    def toggle_status(self, pos: Pos) -> None: ...

    @abc.abstractmethod
    def annotate(self, pos: Pos, name: str | Color) -> None: ...

    @abc.abstractmethod
    def annotate_winrates(self, infos: dict) -> None: ...

    @abc.abstractmethod
    def add_receiver(self, receiver: "BaseReceiver") -> None: ...

    @abc.abstractmethod
    def end_result(self) -> None: ...

    @abc.abstractmethod
    def finish(self) -> None: ...


class Game:
    stones: StonesController
    cursor: Stone

    def __init__(
        self,
        ruleset: Ruleset,  # | None = None,
        stones: StonesController | None = None,
    ):
        self.ruleset = ruleset  # if ruleset else Ruleset(boardsize=9, komi=0.5, handicap=0)
        if not stones:
            stones = StonesController(self.ruleset.boardsize, self.ruleset.handicap)
        assert stones
        self.receivers: List[BaseReceiver] = []
        self.ruleset.set_stonescontroller(stones)
        self.stones = stones
        self._event_threads: List[Thread] = []
        self.last_action_result: ActionResult | None = None
        self._started = False

    def send_game_event(self, result: ActionResult):
        if isinstance(result, ActionResult):
            self.last_action_result = result
        for receiver in self.receivers:
            thread = Thread(target=receiver.receive_game_event, args=(result,))
            self._event_threads.append(thread)
            thread.start()

    def _start(self, receivers: List[BaseReceiver], cursor: Optional[Stone] = None):
        assert not self._started
        self._started = True

        self.receivers = receivers
        if cursor:
            curr = cursor
            while curr:
                if not curr.parent:
                    break
                curr = curr.parent
            self.stones.root = curr
        else:
            self.stones.root = Stone(color=Color.EMPTY, pos=None, parent=None)
            cursor = self.stones.root
        self.stones.set_cursor(cursor)
        self.send_game_event(
            ActionResult(
                type=ActionType.RESET,
                board=self.stones.board,
                stone_result=StoneResult(
                    stone=self.stones.cursor,
                    next_color=self.stones.next_color,
                ),
            )
        )

    def _count(self):
        cnt = Counter(board=self.stones.board)
        coords, killed = cnt.result()
        self.send_game_event(
            ActionResult(
                type=ActionType.COUNT,
                board=self.stones.board,
                game_result=GameResult(
                    winner=None,
                    black=ColorResult(killed=killed[Color.WHITE], coords=coords[Color.BLACK]),
                    white=ColorResult(killed=killed[Color.BLACK], coords=coords[Color.WHITE]),
                    reason="start count",
                ),
            )
        )

    def _place(self, color: Color, pos: Pos | None):
        assert self.last_action_result and self.last_action_result.stone_result
        if not color == self.last_action_result.stone_result.next_color:
            raise WrongColor(f"{color.name}: {pos}")
        result = self.stones.get_result(color, pos, ActionType.STONE)
        try:
            self.ruleset.validate_result(result)
        except ThreePasses:
            self._count()
            return
        except RuleViolation as err:
            print(err)
        else:
            self.stones.apply_result(result)
            self.send_game_event(result)

    def _reset(self, stone: Stone):
        result: ActionResult = self.stones.set_cursor(stone)
        result.type = ActionType.RESET
        self.send_game_event(result)

    def _resign(self, color: Color):
        result = ActionResult(
            board=self.stones.board,
            type=ActionType.RESIGN,
            game_result=GameResult(
                winner=Color.WHITE if color == Color.BLACK else Color.BLACK,
                reason="resign",
            ),
        )
        self.send_game_event(result)

    def callbacks(self) -> AbstractCallbacks:
        game: "Game" = self

        # pylint: disable=protected-access
        class Callbacks(AbstractCallbacks):
            started = False

            def play(self, color: Color, pos: Optional[Pos] = None):
                game._place(color=color, pos=pos)  # pylint: disable=protected-access

            def undo(self):
                if parent := game.stones.cursor.parent:
                    game._reset(parent)  # pylint: disable=protected-access

            def set_cursor(self, stone: Stone):
                game._reset(stone)  # pylint: disable=protected-access

            def resign(self, color: Color):
                game._resign(color)  # pylint: disable=protected-access

            def start(self, receivers: List[BaseReceiver], stone: Optional[Stone] = None):
                assert not self.started
                game._start(receivers=receivers, cursor=stone)  # pylint: disable=protected-access
                self.started = True

            def toggle_status(self, pos):
                chain = game.stones.board.get_chain(pos)
                start = game.stones.board.intersection(pos)
                owner = (
                    None
                    if start.owner
                    else (Color.BLACK if start.color == Color.WHITE else Color.WHITE)
                )
                for cpos in chain:
                    inter = game.stones.board.intersection(cpos)
                    inter.owner = owner
                game._count()  # pylint

            def annotate(self, pos: Pos, name: str | Color | Marker):
                cursor = game.stones.cursor
                if isinstance(name, Color):
                    cursor.annos.stones[pos] = name
                    cursor.apply_permanent_annos(game.stones.board)

                elif isinstance(name, Marker):
                    cursor.annos.markers[pos] = name
                elif isinstance(name, str):
                    if name == "A":
                        cursor.annos.chars[pos] = chr(65 + len(cursor.annos.chars))
                    elif name == "1":
                        cursor.annos.numbers[pos] = str(1 + len(cursor.annos.numbers))

                assert (last := game.last_action_result)
                assert last.stone_result
                action_result = ActionResult(
                    type=ActionType.ANNOTATED,
                    board=game.stones.board,
                    stone_result=StoneResult(
                        next_color=last.stone_result.next_color, stone=last.stone_result.stone
                    ),
                )
                game.send_game_event(action_result)

            def annotate_winrates(self, infos: dict):
                game.stones.cursor.annos.winrates.clear()
                for pos, rate in infos.items():
                    game.stones.cursor.annos.winrates[pos] = rate
                assert (last := game.last_action_result)
                assert last.stone_result
                action_result = ActionResult(
                    type=ActionType.ANNOTATED,
                    board=game.stones.board,
                    stone_result=StoneResult(
                        next_color=last.stone_result.next_color,
                        stone=last.stone_result.stone,
                    ),
                )
                game.send_game_event(action_result)

            def add_receiver(self, receiver: BaseReceiver):
                if receiver not in game.receivers:
                    # receiver.game_callbacks = self
                    game.receivers.append(receiver)

            def end_result(self):
                print("END")

            def finish(self):
                for rec in game.receivers:
                    # rec.__del__()
                    del rec
                print("END")

        return Callbacks()
