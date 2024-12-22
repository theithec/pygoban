import abc
from dataclasses import dataclass
from re import M
from threading import Thread
from typing import TYPE_CHECKING, List, Optional

# from .basecontroller import BaseGameControllerMixin
from .board import Marker
from .receivers import BaseReceiver

# from .results import TurnDone, Event, AnnotationDone, Counted, ColorResult
from . import results
from .rulesets import Counter, Ruleset, RuleViolation, ThreePasses, WrongColor
from .nodescontroller import Color, Pos, Node, NodesController
from .timesettings import PlayerTime


class AbstractCallbacks(abc.ABC):
    """The callbacks a `Game` returns for interacting"""

    @abc.abstractmethod
    def play(self, color: Color, pos: Optional[Pos] = None) -> None: ...

    @abc.abstractmethod
    def undo(self) -> None: ...

    @abc.abstractmethod
    def set_cursor(self, node: Node) -> None: ...

    @abc.abstractmethod
    def start(self, receivers: List["BaseReceiver"], node: Optional[Node] = None) -> None: ...

    @abc.abstractmethod
    def toggle_status(self, pos: Pos) -> None: ...

    @abc.abstractmethod
    def annotate(self, pos: Pos, name: str | Color, next_color: Color) -> None: ...

    @abc.abstractmethod
    def annotate_winrates(self, infos: dict) -> None: ...

    @abc.abstractmethod
    def add_receiver(self, receiver: "BaseReceiver") -> None: ...

    @abc.abstractmethod
    def set_end_result(
        self, result_type: results.GameResultType, color: Color | None = None
    ) -> None: ...

    @abc.abstractmethod
    def quit(self) -> None: ...


class Game:
    """Represents a game of go. A 'game' is any tree of placements/passes"""

    nodes: NodesController
    cursor: Node

    def __init__(
        self,
        ruleset: Ruleset,  # | None = None,
        nodes: NodesController | None = None,
    ):
        self.ruleset = ruleset  # if ruleset else Ruleset(boardsize=9, komi=0.5, handicap=0)
        if not nodes:
            nodes = NodesController(self.ruleset.boardsize, self.ruleset.handicap)
        assert nodes
        self.receivers: List[BaseReceiver] = []
        self.ruleset.set_node_controller(nodes)
        self.nodes = nodes
        self._event_threads: List[Thread] = []
        self._started = False
        self.timers = (
            {
                Color.BLACK: PlayerTime(self, Color.BLACK),
                Color.WHITE: PlayerTime(self, Color.WHITE),
            }
            if ruleset.timesettings
            else None
        )

    def send_game_event(self, result: results.Event):
        """Send the event to all registered recivers"""
        for receiver in self.receivers:
            thread = Thread(target=receiver.receive_game_event, args=(result,))
            self._event_threads.append(thread)
            thread.start()

    def period_ended(self, color: Color, next_time: int):
        """A time period ended"""
        if next_time:
            result: results.Event = results.TimeDone(color=color, next_time=next_time)
        else:
            assert self.timers
            for timer in self.timers.values():
                timer.cancel_timer()
            result_type = results.GameResultType.LOST_BY_TIME
            msg = results.GAME_RESULT_STR_BY_TYPE[result_type].format(color=color.other())
            result = results.GameResultDone(
                winner=color.other(), msg=msg, type=results.GameResultType.LOST_BY_TIME
            )
        self.send_game_event(result)

    def _start(self, receivers: List[BaseReceiver], cursor: Optional[Node] = None):
        """Start a game, sending the emtpy root node"""
        assert not self._started
        self._started = True

        self.receivers = receivers
        if cursor:
            curr = cursor
            while curr:
                if not curr.parent:
                    break
                curr = curr.parent
            self.nodes.root = curr
        else:
            self.nodes.root = Node(color=Color.EMPTY, pos=None, parent=None)
            cursor = self.nodes.root
        result = self.nodes.set_cursor(cursor)
        if self.timers:
            self.timers[result.next_color].start_timer()
        self.send_game_event(result)

    def _count(self):
        """Count a board position"""

        if self.timers:
            for timer in self.timers.values():
                timer.cancel_timer()
        cnt = Counter(board=self.nodes.board)
        coords, killed = cnt.result()
        game_result = results.Counted(
            black=results.ColorResult(killed=killed[Color.WHITE], coords=coords[Color.BLACK]),
            white=results.ColorResult(killed=killed[Color.BLACK], coords=coords[Color.WHITE]),
        )
        self.send_game_event(game_result)

    def _place(self, color: Color, pos: Pos | None) -> None:
        """Placement of a stone or a pass if `pos` is None"""
        result = self.nodes.get_result(color, pos)
        try:
            self.ruleset.validate_result(result)
        except ThreePasses:
            self._count()
            return
        except RuleViolation as err:
            print(err)
        else:
            self.nodes.apply_result(result)
            if self.timers:
                own_timer = self.timers[result.next_color]
                if not own_timer.ended:
                    own_timer.start_timer()
                self.nodes.cursor.annos.time_left = own_timer.nexttime()
                other_timer = self.timers[result.next_color.other()]
                if not other_timer.ended:
                    other_timer.cancel_timer()
            self.send_game_event(result)

    def _reset(self, node: Node):
        """Reset the board to given Situation"""
        import time

        start = time.time()
        result: results.TurnDone = self.nodes.set_cursor(node)
        end = time.time()
        print("RESET", end - start)
        self.send_game_event(result)

    def callbacks(self) -> AbstractCallbacks:
        """Return the callbacks for a game"""
        game: "Game" = self

        # pylint: disable=protected-access
        class Callbacks(AbstractCallbacks):
            started = False

            def play(self, color: Color, pos: Optional[Pos] = None):
                game._place(color=color, pos=pos)  # pylint: disable=protected-access

            def undo(self):
                if parent := game.nodes.cursor.parent:
                    game._reset(parent)  # pylint: disable=protected-access

            def set_cursor(self, node: Node):
                game._reset(node)  # pylint: disable=protected-access

            def start(self, receivers: List[BaseReceiver], node: Optional[Node] = None):
                assert not self.started
                game._start(receivers=receivers, cursor=node)  # pylint: disable=protected-access
                self.started = True

            def toggle_status(self, pos):
                chain = game.nodes.board.get_chain(pos)
                start = game.nodes.board.intersection(pos)
                owner = (
                    None
                    if start.owner
                    else (Color.BLACK if start.color == Color.WHITE else Color.WHITE)
                )
                for cpos in chain:
                    inter = game.nodes.board.intersection(cpos)
                    inter.owner = owner
                game._count()  # pylint

            def annotate(self, pos: Pos, name: str | Color | Marker, next_color: Color):
                cursor = game.nodes.cursor
                if isinstance(name, Color):
                    cursor.annos.stones[pos] = name
                    cursor.apply_permanent_annos(game.nodes.board)

                elif isinstance(name, Marker):
                    cursor.annos.markers[pos] = name
                elif isinstance(name, str):
                    if name == "A":
                        cursor.annos.chars[pos] = chr(65 + len(cursor.annos.chars))
                    elif name == "1":
                        cursor.annos.numbers[pos] = str(1 + len(cursor.annos.numbers))

                action_result = results.AnnotationDone()
                game.send_game_event(action_result)

            def annotate_winrates(self, infos: dict):
                game.nodes.cursor.annos.winrates.clear()
                for pos, rate in infos.items():
                    game.nodes.cursor.annos.winrates[pos] = rate
                assert (last := game.last_action_result)
                assert last.stone_result
                action_result = ActionResult(
                    type=ActionType.ANNOTATED,
                    board=game.nodes.board,
                    stone_result=StoneResult(
                        next_color=last.stone_result.next_color,
                        node=last.stone_result.node,
                    ),
                )
                game.send_game_event(action_result)

            def add_receiver(self, receiver: BaseReceiver):
                if receiver not in game.receivers:
                    # receiver.game_callbacks = self
                    game.receivers.append(receiver)

            def set_end_result(self, result_type, color: Color | None = None):
                print("Print TODO WRITE RESULT")
                if game.timers:
                    for timer in game.timers.values():
                        timer.cancel_timer()

                types = results.GameResultType
                fmt = results.GAME_RESULT_STR_BY_TYPE[result_type]
                msg = ""
                match result_type:
                    case types.LOST_BY_TIME | types.RESIGN:
                        assert color
                        winner = color.other()
                        msg = fmt.format(color=winner)
                    case types.COUNTED:
                        cnt = Counter(board=game.nodes.board)
                        coords, killed = cnt.result()
                        for color in (Color.BLACK, Color.WHITE):
                            killed[color] += game.nodes.total_dead[color.other()] + len(
                                coords[color]
                            )
                        killed[Color.WHITE] += game.ruleset.komi
                        winner = max(killed, key=killed.get)
                        points_diff = killed[winner] - killed[winner.other()]

                        msg = fmt.format(color=winner, points_diff=points_diff)

                result = results.GameResultDone(winner=winner, msg=msg, type=result_type)
                game.send_game_event(result)

            def quit(self):
                for rec in game.receivers:
                    # rec.__del__()
                    del rec
                print("END")

        return Callbacks()
